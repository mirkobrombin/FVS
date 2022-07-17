import os
import yaml
import logging

from fvs.exceptions import FVSNothingToCommit, FVSCallerWrongClass, FVSEmptyCommitMessage, FVSWrongUnstagedDict, \
    FVSStateNotFound, FVSCommittingToExistingState
from fvs.data import FVSData
from fvs.file import FVSFile
from fvs.utils import FVSUtils


logger = logging.getLogger("fvs.state")


class FVSState:
    __files: dict = None
    __state_id: int = None
    __state_path: str = None

    def __init__(self, repo:'FVSRepo', state_id: int = None):
        self.__repo = repo
        self.__files = {"count": 0, "added": {}, "modified": {}, "removed": {}, "relative_paths_in_state": []}
        
        if state_id is not None:
            self.__load_state(state_id)
    
    @classmethod
    def load(cls, repo:'FVSRepo', state_id:int):
        """
        This constructor will return a new FVSState object for the given
        state_id.
        """
        return cls(repo, state_id)
    
    def __load_state(self, state_id:int):
        """
        This method will load a state from the repository.
        """
        self.__state_id = state_id
        self.__state_path = os.path.join(self.__repo.states_path, str(state_id))

        if not os.path.exists(self.__state_path):
            raise FVSStateNotFound(state_id)

        with open(os.path.join(self.__state_path, "files.yml"), "r") as f:
            self.__files = yaml.safe_load(f)
    
    def commit(
        self,
        message:str,
        unstaged_files:dict,
        ignore:list = None
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
        want untrackable commits.
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
            unstaged_files.get("removed")
        ]:
            raise FVSWrongUnstagedDict()

        """
        For the same reason above, we will check if ignore is None. If it is,
        we will create an empty list.
        """
        if ignore is None:
            ignore = []
        
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
            fvs_data.add_file(FVSFile(self.__repo, _file["file_name"], _file["md5"], _file["relative_path"]))
            self.__files["added"][_file["md5"]] = {
                "file_name": _file["file_name"],
                "md5": _file["md5"],
                "relative_path": _file["relative_path"],
            }
            self.__files["relative_paths_in_state"].append(_file["relative_path"])
        
        for _file in unstaged_files["modified"]:
            fvs_data.add_file(FVSFile(self.__repo, _file["file_name"], _file["md5"], _file["relative_path"]))
            self.__files["modified"][_file["md5"]] = {
                "file_name": _file["file_name"],
                "md5": _file["md5"],
                "relative_path": _file["relative_path"],
            }
            self.__files["relative_paths_in_state"].append(_file["relative_path"])
        
        for _file in unstaged_files["removed"]:
            self.__files["removed"][_file["md5"]] = {
                "file_name": _file["file_name"],
                "md5": _file["md5"],
                "relative_path": _file["relative_path"],
            }
        fvs_data.complete_transaction()
        self.__save_state()
    
    def __save_state(self):
        """
        This method will save the state to the repository.
        """
        state_path = self.__repo.new_state_path_by_id(self.__state_id)
        with open(os.path.join(state_path, "files.yml"), "w") as f:
            yaml.dump(self.__files, f, sort_keys=False)
    
    def has_file(self, file_name:str, md5:str):
        """
        This method will check if the state has the given file.
        """
        if md5 in self.__files["added"] or md5 in self.__files["modified"]:
            return True
        return False
    
    def has_relative_path(self, relative_path:str):
        """
        This method will check if the state has the given relative path.
        """
        if relative_path in self.__files["relative_paths_in_state"]:
            return True
        return False

    def __is_initialized(self):
        """
        This method will check if the state is initialized.
        """
        try:
            self.__repo.is_valid_state(self.__repo.next_state_id)
        except FVSStateNotFound:
            return False
        return True

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
