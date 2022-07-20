import os
import orjson
import logging

from fvs.exceptions import FVSCallerWrongClass, FVSEmptyCommitMessage, FVSWrongUnstagedDict, \
    FVSStateNotFound, FVSCommittingToExistingState, FVSUnsupportedKey
from fvs.data import FVSData
from fvs.file import FVSFile
from fvs.utils import FVSUtils

logger = logging.getLogger("fvs.state")


class FVSState:
    __files: dict = None
    __state_id: int = None
    __state_path: str = None

    def __init__(self, repo: 'FVSRepo', state_id: int = None):
        self.__repo = repo
        self.__files = {"count": 0, "added": {}, "modified": {}, "removed": {}, "intact": {}}

        if state_id is not None:
            self.__load_state(state_id)

    @classmethod
    def load(cls, repo: 'FVSRepo', state_id: int):
        """
        This constructor will return a new FVSState object for the given
        state_id.
        """
        return cls(repo, state_id)

    def __load_state(self, state_id: int):
        """
        This method will load a state from the repository.
        """
        self.__state_id = state_id
        self.__state_path = os.path.join(self.__repo.states_path, str(state_id))
        if not os.path.exists(self.__state_path):
            raise FVSStateNotFound(state_id)

        with open(os.path.join(self.__state_path, "files.json"), "r") as f:
            self.__files = orjson.loads(f.read())
        
    def commit(
            self,
            message: str,
            unstaged_files: dict
    ):
        """
        States are supposed to be committed only from FVSRepo and only on first
        initialization. So here we will check if the caller is the expected
        class.
        """
        if FVSUtils.get_caller_class_name() != "FVSRepo":
            raise FVSCallerWrongClass("FVSRepo")

        """
        For the same reason above, we will check if the state were already
        initialized to avoid unwanted commits.
        """
        if self.__is_initialized():
            raise FVSCommittingToExistingState()

        """
        As a rule in FVS, the commit message should not be empty. We don't
        want untraceable commits.
        """
        if message in [None, ""]:
            raise FVSEmptyCommitMessage()

        """
        To avoid further investigation and multiple checks, we will check
        for the unstaged files dict structure. It must contain the following
        keys: added, modified, removed.
        """
        if False in [
            unstaged_files.get("count"),
            unstaged_files.get("added"),
            unstaged_files.get("modified"),
            unstaged_files.get("removed"),
            unstaged_files.get("intact")
        ]:
            raise FVSWrongUnstagedDict()

        """
        Set the state id with the next state id available in the repository.
        """
        self.__state_id = self.__repo.next_state_id
        self.__files["count"] = unstaged_files["count"]

        """
        Instantiate the FVSData class and start collecting the files.
        """
        fvs_data = FVSData(self.__repo, self)

        for _file in unstaged_files["added"]:
            fvs_data.add_file(FVSFile(self.__repo, _file["file_name"], _file["sha1"], [_file["relative_path"]]))
            if _file["sha1"] in self.__files["added"]:
                self.__files["added"][_file["sha1"]]["relative_paths"] += [_file["relative_path"]]
            else:
                self.__files["added"][_file["sha1"]] = {
                    "file_name": _file["file_name"],
                    "sha1": _file["sha1"],
                    "relative_paths": [_file["relative_path"]],
                }

        for _file in unstaged_files["modified"]:
            fvs_data.add_file(FVSFile(self.__repo, _file["file_name"], _file["sha1"], [_file["relative_path"]]))
            if _file["sha1"] in self.__files["modified"]:
                self.__files["modified"][_file["sha1"]]["relative_paths"] += [_file["relative_path"]]
            else:
                self.__files["modified"][_file["sha1"]] = {
                    "file_name": _file["file_name"],
                    "sha1": _file["sha1"],
                    "relative_paths": [_file["relative_path"]],
                }

        for _file in unstaged_files["removed"]:
            fvs_data.delete_file(FVSFile(self.__repo, _file["file_name"], _file["sha1"], [_file["relative_path"]]))
            if _file["sha1"] in self.__files["removed"]:
                self.__files["removed"][_file["sha1"]]["relative_paths"] += [_file["relative_path"]]
            else:
                self.__files["removed"][_file["sha1"]] = {
                    "file_name": _file["file_name"],
                    "sha1": _file["sha1"],
                    "relative_paths": [_file["relative_path"]],
                }

        for _file in unstaged_files["intact"]:
            if _file["sha1"] in self.__files["intact"]:
                self.__files["intact"][_file["sha1"]]["relative_paths"] += [_file["relative_path"]]
            else:
                self.__files["intact"][_file["sha1"]] = {
                    "file_name": _file["file_name"],
                    "sha1": _file["sha1"],
                    "relative_paths": [_file["relative_path"]],
                }

        fvs_data.complete_transaction()
        self.__save_state()

    def break_references(self):
        """
        This method ask to FVSData to remove the reference to the state for 
        all the files, it will also physical delete the file if it has
        no other referenced states.
        """
        if FVSUtils.get_caller_class_name() != "FVSRepo":
            raise FVSCallerWrongClass("FVSRepo")

        fvs_data = FVSData(self.__repo, self)

        for _file in self.__files["added"].values():
            fvs_data.delete_file(FVSFile(self.__repo, _file["file_name"], _file["sha1"], _file["relative_paths"]))

        for _file in self.__files["modified"].values():
            fvs_data.delete_file(FVSFile(self.__repo, _file["file_name"], _file["sha1"], _file["relative_paths"]))

        fvs_data.complete_transaction()

    def has_file(self, sha1: str, relative_path: str):
        """
        This method will check if the state has the given file.
        """
        if sha1 in self.__files["added"]:
            if relative_path in self.__files["added"][sha1]["relative_paths"]:
                return True
        if sha1 in self.__files["modified"]:
            if relative_path in self.__files["modified"][sha1]["relative_paths"]:
                return True
        if sha1 in self.__files["intact"]:
            if relative_path in self.__files["intact"][sha1]["relative_paths"]:
                return True
                
        return False

    def __save_state(self):
        """
        This method will save the state to the repository.
        """
        state_path = self.__repo.new_state_path_by_id(self.__state_id)
        with open(os.path.join(state_path, "files.json"), "wb") as f:
            f.write(orjson.dumps(self.__files, f, option=orjson.OPT_NON_STR_KEYS,))

    def __is_initialized(self):
        """
        This method will check if the state is initialized.
        """
        try:
            self.__repo.is_valid_state(self.__repo.next_state_id)
        except FVSStateNotFound:
            return False
        return True

    def has_relative_path(self, relative_path: str, key: str = "any"):
        """
        This method will return the entry from the state files which
        corresponds to the given file name. The 'any' key will check in
        added, modified and intact files.
        """
        supported_keys = ["any", "added", "modified", "intact"]
        if key not in supported_keys:
            raise FVSUnsupportedKey(supported_keys)

        if key == "any":
            for file in self.__files["added"].values():
                if relative_path in file["relative_paths"]:
                    return file
            for file in self.__files["modified"].values():
                if relative_path in file["relative_paths"]:
                    return file
            for file in self.__files["intact"].values():
                if relative_path in file["relative_paths"]:
                    return file
        else:
            for _file in self.__files[key].values():
                if relative_path in _file["relative_paths"]:
                    return _file
        return None

    @property
    def files(self):
        """
        This method will return the files in the state.
        """
        return self.__files

    @property
    def state_id(self):
        """
        This method will return the state id.
        """
        return self.__state_id

    @property
    def state_path(self):
        """
        This method will return the state path.
        """
        return self.__state_path
