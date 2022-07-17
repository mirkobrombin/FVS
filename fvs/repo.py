import os
import yaml
import hashlib
import logging

from fvs.exceptions import FVSNothingToCommit, FVSEmptyCommitMessage, FVSStateNotFound, FVSMissingStateIndex
from fvs.pattern import FVSPattern
from fvs.state import FVSState
from fvs.utils import FVSUtils

logger = logging.getLogger("fvs.repo")

class FVSRepo:
    __repo_conf: dict = None
    __has_no_states: bool = False

    def __init__(self, repo_path: str):
        """
        Initialize the FVSRepo.
        """
        self.__repo_path = repo_path
        self.__states_path = os.path.join(self.__repo_path, ".fvs/states")
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
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.yml")
        updated = False
        for dir in dirs:
            if not os.path.exists(os.path.join(self.__repo_path, dir)):
                os.makedirs(os.path.join(self.__repo_path, dir))
                updated = True

        if not os.path.exists(repo_conf):
            with open(repo_conf, "w") as f:
                self.__repo_conf = {"id": -1, "states": {}}
                yaml.dump(self.__repo_conf, f, sort_keys=False)
                updated = True
        
        if updated:
            logger.debug(f"FVS path updated for repository {self.__repo_path}")
    
    def __load_config(self):
        """
        Load the repository configuration.
        """
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.yml")
        with open(repo_conf, "r") as f:
            self.__repo_conf = yaml.safe_load(f)

        self.__states = self.__repo_conf["states"]
        if self.__repo_conf["id"] >= 0:
            self.__active_state = FVSState(self, self.__repo_conf["id"])
        else:
            self.__has_no_states = True
        
    def get_unstaged_files(self, ignore: list = []):
        """
        Get the unstaged files.
        """
        unstaged_files = {
            "count": 0,
            "added": [],
            "removed": [],
            "modified": []
        }
        
        for root, dirs, files in os.walk(self.__repo_path):
            """
            Here we are excluding the .fvs/ directory from the unstaged files
            because we don't want to invoke the monster of loops.
            """
            if ".fvs" in root:  # TODO: need to be improved
                continue
        
            """
            The following new variable is used to store all relative paths
            handled in the following loop. We will use them to list removed
            files.
            """
            unstaged_relative_paths = []

            """
            Here we loop through the ignore pattern and remove the files that
            match any of them. Check if performed on the relative path.
            """
            for pattern in ignore:
                files = [f for f in files if not FVSPattern.match(pattern, self.__get_relative_path(f))]

            """
            Here we loop through the files and determinate which ones are
            added, removed or modified, comparing with prior state or simply
            adding all of them if this is the first state.
            """
            for file in files:
                _full_path = os.path.join(root, file)
                _relative_path = self.__get_relative_path(file)
                _md5 = FVSUtils.get_md5_hash(_full_path)
                unstaged_relative_paths.append(_relative_path)

                if not self.__has_no_states and self.__active_state.has_file(file, _md5):
                    continue

                if not self.__has_no_states and self.__active_state.has_relative_path(_relative_path):
                    unstaged_files["modified"].append({
                        "file_name": file, 
                        "md5": _md5, 
                        "relative_path": _relative_path
                    })
                else:
                    unstaged_files["added"].append({
                        "file_name": file, 
                        "md5": _md5, 
                        "relative_path": _relative_path
                    })
                unstaged_files["count"] += 1

            if not self.__has_no_states:
                for rel in self.__active_state.files["relative_paths_in_state"]:
                    if rel not in unstaged_relative_paths:
                        unstaged_files["removed"].append(file)
                        unstaged_files["count"] += 1

        return unstaged_files
    
    def commit(self, message: str, ignore: list=None):
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
        
        if ignore is None:
            ignore = []

        unstaged_files = self.get_unstaged_files(ignore)
        if unstaged_files["count"] == 0:
            raise FVSNothingToCommit()
        
        # Create a new state
        state = FVSState(self)
        state.commit(message, unstaged_files, ignore)
        self.__states[state.state_id] = message
        self.__active_state = state
        self.__update_repo()
        return state

    def restore(self, state_id: int):
        """
        Restore the state with the given id.
        """
        print("Not implemented yet.")
        return
    
    def is_valid_state(self, state_id: int):
        """
        Check if the state with the given id is valid.
        ...
        Raises:
            FVSStateNotFound: If the state with the given id does not exist.
            FVSMissingStateIndex: If the state with the given id is missing
            FVSEmptyStateIndex: If the state with the given id is empty.
        """
        index_path = os.path.join(self.get_state_path(state_id), "files.yml")

        if not os.path.exists(self.get_state_path(state_id)):
            raise FVSStateNotFound(state_id)

        if not os.path.exists(index_path):
            raise FVSMissingStateIndex(state_id)
        
        with open(index_path, "r") as f:
            index = yaml.safe_load(f)

        if not index:
            raise FVSEmptyStateIndex(state_id)

        return True
    
    def __get_relative_path(self, path: str):
        """
        Get the relative path of the given files.
        """
        return os.path.join(
            os.path.dirname(self.__repo_path),
            path
        )

    def get_state_path(self, state_id: int):
        """
        Get the path of the state with the given id.
        """
        return os.path.join(self.__states_path, str(state_id))
    
    def __update_repo(self):
        """
        Update the repository configuration.
        """
        repo_conf = os.path.join(self.__repo_path, ".fvs/repo.yml")
        with open(repo_conf, "w") as f:
            self.__repo_conf["id"] = self.__active_state.state_id
            self.__repo_conf["states"] = self.__states
            yaml.dump(self.__repo_conf, f, sort_keys=False)
        
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
        return len(self.__states.keys())
    
    @property
    def active_state(self):
        """
        Get the active state.
        """
        return self.__active_state
    
    @property
    def states(self):
        """
        Get the list of states.
        """
        return self.__states
