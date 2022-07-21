import os
import time
import orjson
import shutil
import logging

from fvs.exceptions import FVSNothingToCommit, FVSEmptyCommitMessage, FVSStateNotFound, FVSMissingStateIndex, \
    FVSNothingToRestore, FVSStateZeroNotDeletable, FVSEmptyStateIndex, FVSStateAlreadyExists
from fvs.pattern import FVSPattern
from fvs.state import FVSState
from fvs.file import FVSFile
from fvs.data import FVSData
from fvs.utils import FVSUtils

logger = logging.getLogger("fvs.repo")


class FVSRepo:
    __repo_conf: dict = None
    __has_no_states: bool = False
    __use_compression = False
    __active_state: 'FVSState' = None

    def __init__(self, repo_path: str, use_compression: bool = False):
        """
        Initialize the FVSRepo.
        """
        self.__repo_path = os.path.abspath(repo_path)
        self.__states_path = os.path.join(self.__repo_path, ".fvs/states")
        self.__use_compression = use_compression
        self.__update_fvs_path()
        self.__load_config()

    def __update_fvs_path(self):
        """
        Update the path of the .fvs directory. This directory is not meant
        to be edited outside/manually. Here we just create it if it doesn't
        exist and try to fix it if wrong.
        """
        dirs = [
            ".fvs",
            ".fvs/states",
            ".fvs/data",
        ]
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.json")
        updated = False
        for _dir in dirs:
            if not os.path.exists(os.path.join(self.__repo_path, _dir)):
                os.makedirs(os.path.join(self.__repo_path, _dir))
                updated = True

        if not os.path.exists(repo_conf):
            with open(repo_conf, "wb") as f:
                self.__repo_conf = {"id": -1, "states": {}, "compression": self.__use_compression}
                f.write(orjson.dumps(self.__repo_conf, f, option=orjson.OPT_NON_STR_KEYS,))
                updated = True

        if updated:
            logger.debug(f"FVS path updated for repository {self.__repo_path}")

    def __load_config(self):
        """
        Load the repository configuration.
        """
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.json")
        with open(repo_conf, "r") as f:
            self.__repo_conf = orjson.loads(f.read())

        """
        JSON store int key as strings, so we need to convert them back to int.
        """
        self.__states = {int(key): value for key, value in self.__repo_conf["states"].items()}

        if int(self.__repo_conf["id"]) >= 0:
            self.__active_state = FVSState(self, int(self.__repo_conf["id"]))
        else:
            self.__has_no_states = True
        
        self.__use_compression = self.__repo_conf["compression"]

    def get_unstaged_files(self, ignore: list = None, purpose: int = 0):
        """
        Get the unstaged files.
        ...
        Purpose values:
            0: Committing a new state.
            1: Restoring a state (will return original sha1 for modified files)
        """
        unstaged_files = {
            "count": 0,
            "added": [],
            "removed": [],
            "modified": [],
            "intact": []
        }
        active_state_files = {}

        if ignore is None:
            ignore = []

        """
        The following new variable is used to store all relative paths
        handled in the following loop. We will use them to list removed
        files.
        """
        unstaged_relative_paths = []

        """
        Create a copy of the active state files so we can remove every
        handled entry and easily figure out what was deleted.
        """
        if not self.__has_no_states:
            active_state_files = self.__active_state.files.copy()
        else:
            active_state_files = {"added": {}, "removed": {}, "modified": {}, "intact": {}}

        def del_active_state_file_key(sha1: str):
            active_state_files["added"].pop(sha1, None)
            active_state_files["modified"].pop(sha1, None)
            active_state_files["intact"].pop(sha1, None)
        
        for root, _, files in os.walk(self.__repo_path):
            """
            Here we are excluding the .fvs/ directory from the unstaged files
            because we don't want to invoke the monster of loops.
            """
            if ".fvs" in root.split(os.sep):
                continue

            """
            Here we loop through the files and determinate which ones are
            added, removed, modified or intact, comparing with prior state 
            or simply adding all of them if this is the first state.
            """
            for file in files:
                _full_path = os.path.join(root, file)
                _relative_path = self.__get_relative_path(os.path.join(root, file))

                """
                Here we loop through the ignore pattern and remove the files that
                match any of them. Check if performed on the relative path.
                """
                if FVSPattern.match(ignore, _relative_path):
                    continue

                _sha1 = FVSUtils.get_sha1_hash(_full_path)
                _entry = {
                    "file_name": file,
                    "sha1": _sha1,
                    "relative_path": _relative_path
                }

                unstaged_relative_paths.append(_relative_path)

                """
                If this is the first state, just add all files.
                """
                if self.__has_no_states:
                    unstaged_files["added"].append(_entry)
                    unstaged_files["count"] += 1
                    continue

                """
                Assuming this is not the first state, we need to check if
                the file is added, removed, modified or intact.
                """
                if self.__active_state.has_file(_sha1, _relative_path):
                    unstaged_files["intact"].append(_entry)
                elif orig := self.__active_state.has_relative_path(_relative_path):
                    if purpose == 1:
                        _sha1 = orig["sha1"]
                    unstaged_files["modified"].append({
                        "file_name": file,
                        "sha1": _sha1,
                        "relative_path": _relative_path
                    })
                    unstaged_files["count"] += 1
                    print(f"{_relative_path}is modified")
                else:
                    unstaged_files["added"].append(_entry)
                    unstaged_files["count"] += 1

                unstaged_relative_paths.append(_relative_path)

        if not self.__has_no_states:
            for file in list(active_state_files["added"].values()) + \
                        list(active_state_files["modified"].values()) + \
                        list(active_state_files["intact"].values()):
                for relative_path in file["relative_paths"]:
                    if relative_path not in unstaged_relative_paths:
                        unstaged_files["removed"].append({
                            "file_name": file["file_name"],
                            "sha1": file["sha1"],
                            "relative_path": relative_path
                        })
                        unstaged_files["count"] += 1

        return unstaged_files

    def commit(self, message: str, ignore: list = None):
        """
        Commit the current state. This is a wrapper around the commit method
        of the FVSState class. A wrapper is used to store the state message
        and process staged files before committing.
        ...
        Raises:
            FVSEmptyCommitMessage: If the message is empty.
            FVSNothingToCommit: If there are no unstaged files.
        """
        if message in [None, ""]:
            raise FVSEmptyCommitMessage()

        unstaged_files = self.get_unstaged_files(ignore)
        if unstaged_files["count"] == 0:
            raise FVSNothingToCommit()

        # Create a new state
        state = FVSState(self)
        state.commit(message, unstaged_files)
        self.__states[state.state_id] = {
            "message": message,
            "timestamp": time.time()
        }
        self.__active_state = state
        self.__update_repo()
        return {
            "state_id": state.state_id,
            "message": message,
            "timestamp": time.time(),
            "added": len(unstaged_files["added"]),
            "removed": len(unstaged_files["removed"]),
            "modified": len(unstaged_files["modified"]),
            "intact": len(unstaged_files["intact"])
        }

    def delete_state(self, state_id: int, update_repo: bool = True):
        """
        Delete a state and all its subsequent states.
        ...
        Raises:
            FVSStateZeroNotDeletable: If the state_id is 0.
            FVSStateNotFound: If the state doesn't exist.
        """
        if int(state_id) == 0:
            raise FVSStateZeroNotDeletable()

        if int(state_id) not in self.__states:
            raise FVSStateNotFound(state_id)

        """
        Traveling in the future is probably something we don't want to do. So
        we will break references for subsequent states too.
        """
        for _state_id in [state_id] + self.__get_subsequent_state_ids(state_id):
            state = FVSState(self, _state_id)
            state.break_references()

            """
            If the state is the active state, we need to set the active state to
            the previous one.
            """
            if self.__active_state.state_id == _state_id:
                self.__active_state = FVSState(self, self.__get_prior_state_id(_state_id))

            """
            Delete the state from the states folder. It should be safer now as
            we already unreferenced the state from all its files.
            """
            self.__delete_state_folder(state)
            del self.__states[_state_id]

        if update_repo:
            self.__update_repo()

    def delete_active_state(self):
        """
        Delete the active state.
        """
        self.delete_state(self.__active_state.state_id)

    def restore_state(self, state_id: int, ignore: list = None):
        """
        Restore the state with the given id. This will remove all unstaged
        files and restore the given state, deleting any subsequent states.
        ...
        Raises:
            FVSStateNotFound: If the state doesn't exist.
            FVSNothingToRestore: If there are no unstaged files.
        """
        if int(state_id) not in self.__states.keys():
            raise FVSStateNotFound(state_id)

        self.__active_state = FVSState(self, state_id)
        subsequent_state_id = self.__get_subsequent_state_id(state_id)
        unstaged_files = self.get_unstaged_files(ignore, purpose=1)

        if unstaged_files["count"] == 0:
            raise FVSNothingToRestore()

        """
        If the given state has subsequent states, we need to delete them. The
        following call will start breaking references for the first subsequent
        state, FVSData will take care of the rest, physically deleting the
        files when the reference count reaches 0 (no state references).
        """
        if subsequent_state_id is not None:
            self.delete_state(subsequent_state_id, False)

        """
        Here we restore the situation to the given state, removing all
        unstaged files.
        """
        fvs_data = FVSData(self)

        for file in unstaged_files["added"]:
            _file_path = os.path.join(self.__repo_path, file["relative_path"])
            if os.path.isdir(_file_path):
                shutil.rmtree(_file_path)
            else:
                os.remove(_file_path)

        for file in unstaged_files["modified"]:
            internal_path = fvs_data.get_int_path(file["file_name"])
            FVSFile(self, file["file_name"], file["sha1"], [file["relative_path"]]).restore(internal_path)

        for file in unstaged_files["removed"]:
            internal_path = fvs_data.get_file_location(file["sha1"])
            FVSFile(self, file["file_name"], file["sha1"], [file["relative_path"]]).restore(internal_path)

        self.__update_repo()

    @staticmethod
    def __delete_state_folder(state: FVSState):
        """
        Delete the state folder with the given id.
        """
        shutil.rmtree(state.state_path)

    def is_valid_state(self, state_id: int):
        """
        Check if the state with the given id is valid.
        ...
        Raises:
            FVSStateNotFound: If the state with the given id does not exist.
            FVSMissingStateIndex: If the state with the given id is missing
            FVSEmptyStateIndex: If the state with the given id is empty.
        """
        index_path = os.path.join(self.get_state_path(state_id), "files.json")

        if not os.path.exists(self.get_state_path(state_id)):
            raise FVSStateNotFound(state_id)

        if not os.path.exists(index_path):
            raise FVSMissingStateIndex(state_id)

        with open(index_path, "r") as f:
            index = orjson.loads(f.read())

        if not index:
            raise FVSEmptyStateIndex(state_id)

        return True

    def __get_prior_state_id(self, state_id: int):
        """
        Get the id of the prior state.
        ...
        Raises:
            FVSStateNotFound: If the state with the given id does not exist.
        """
        if int(state_id) not in self.__states.keys():
            raise FVSStateNotFound(state_id)

        for key in self.__states.keys():
            if key < state_id:
                return key

        return 0

    def __get_subsequent_state_ids(self, state_id: int):
        """
        Get the ids of the subsequent states.
        ...
        Raises:
            FVSStateNotFound: If the state with the given id does not exist.
        """
        if int(state_id) not in self.__states.keys():
            raise FVSStateNotFound(state_id)

        subsequent_states = []
        for key in self.__states.keys():
            if key > int(state_id):
                subsequent_states.append(key)

        return subsequent_states

    def __get_subsequent_state_id(self, state_id: int):
        """
        Get the id of the subsequent state.
        ...
        Raises:
            FVSStateNotFound: If the state with the given id does not exist.
        """
        if int(state_id) not in self.__states.keys():
            raise FVSStateNotFound(state_id)

        for key in self.__states.keys():
            if key > int(state_id):
                return key

        return 0

    def __get_relative_path(self, path: str):
        """
        Get the relative path of the given files.
        """
        repo_root = os.path.dirname(self.__repo_path)
        return os.path.relpath(path, self.__repo_path)

    def get_state_path(self, state_id: int):
        """
        Get the path of the state with the given id.
        """
        return os.path.join(self.__states_path, str(state_id))

    def __update_repo(self):
        """
        Update the repository configuration.
        """
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.json")
        with open(repo_conf, "wb") as f:
            self.__repo_conf["id"] = self.__active_state.state_id
            self.__repo_conf["states"] = self.__states
            f.write(orjson.dumps(self.__repo_conf, f, option=orjson.OPT_NON_STR_KEYS,))

        if self.__has_no_states:
            self.__has_no_states = False

    def new_state_path_by_id(self, state_id: int):
        """
        Get the path of the state with the given id.
        ...
        Raises:
            FVSStateAlreadyExists: If the state already exists.
        """
        state_path = os.path.join(self.__states_path, str(state_id))
        if os.path.exists(state_path):
            raise FVSStateAlreadyExists(state_id)
        os.makedirs(state_path)
        return state_path

    @property
    def repo_path(self):
        """
        Get the repository path.
        """
        return self.__repo_path

    @property
    def states_path(self):
        """
        Get the path of the states.
        """
        return self.__states_path

    @property
    def next_state_id(self):
        """
        Get the next state id.
        """
        if self.__has_no_states:
            return 0
        return list(self.__states)[-1] + 1

    @property
    def active_state_id(self):
        """
        Get the active state.
        """
        if self.__active_state is None:
            return None
        return self.__active_state.state_id

    @property
    def states(self):
        """
        Get the list of states.
        """
        return self.__states
    
    @property
    def has_compression(self):
        """
        Get the compression status.
        """
        return self.__use_compression
