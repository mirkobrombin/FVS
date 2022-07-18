import os
import yaml
import logging

from fvs.exceptions import FVSStateDataHasNoState, VFSTransactionAlreadyStarted


logger = logging.getLogger("fvs.data")


class FVSData:
    __data_conf: dict = None
    __data_conf_path: str = None
    __data_int_paths: list = [
        "a","b","c","d","e","f","g","h","i","j","k","l","m",
        "n","o","p","q","r","s","t","u","v","w","x","y","z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-"
    ]
    __state:'FVSState' = None
    __transaction: list = None
    __transaction_type: int = None  # 0: add, 1: remove

    def __init__(self, repo: 'FVSRepo', state: 'FVSState'=None):
        """
        Initialize the FVSData.
        """
        self.__data_path = os.path.join(repo.repo_path, ".fvs/data")
        self.__state = state
        self.__update_fvs_path()
        self.__load_config()

    def __update_fvs_path(self):
        """
        Update the structure of path data/ in the FVS repository. This also
        performs some checks to ensure that the data/ directory is valid,
        fixing it if necessary.
        """
        self.__data_conf_path = os.path.join(self.__data_path, "data.yml")

        """
        This check if the data/ directory exists. If not, create it.
        """
        if not os.path.exists(self.__data_path):
            os.makedirs(os.path.join(self.__data_path, dir))
        
        """
        This check if internal paths (__data_int_paths) exist. If not, 
        create them.
        """
        for int_path in self.__data_int_paths:
            if not os.path.exists(os.path.join(self.__data_path, int_path)):
                os.makedirs(os.path.join(self.__data_path, int_path))

        """
        Check if the data.yml file exists. If not, create it and write the
        default configuration.
        """
        if not os.path.exists(self.__data_conf_path):
            with open(self.__data_conf_path, "w") as f:
                self.__data_conf = {}
                yaml.dump(self.__data_conf, f, sort_keys=False)

    def __load_config(self):
        """
        Load the data configuration from the data/data.yml file.
        """
        with open(self.__data_conf_path, "r") as f:
            self.__data_conf = yaml.safe_load(f)

    def __save_config(self):
        """
        Save the data configuration to the data/data.yml file.
        """
        with open(self.__data_conf_path, "w") as f:
            yaml.dump(self.__data_conf, f, sort_keys=False)
    
    def complete_transaction(self):
        """
        Complete the transaction duplicating the files in the proper internal
        data path. It also saves the configuration to the data/data.yml file.
        """
        for file in self.__transaction:
            file.copy_to(self.get_int_path(file.file_name))

        self.__save_config()
    
    def get_int_path(self, file_name: str):
        """
        This simple method determines the internal path of a file based
        on the first letter of the file name. Every file starting with
        a special character will be placed in the "-" directory.
        """
        first_letter = file_name[0].lower()
        int_path = "-"
        if first_letter in self.__data_int_paths:
            int_path = first_letter
        
        return os.path.join(self.__data_path, int_path)
    
    def __set_transaction_type(self, type_id: int):
        if self.__transaction is None:
            self.__transaction = []
            if self.__transaction_type is None:
                self.__transaction_type = type_id
            elif self.__transaction_type != type_id:
                raise VFSTransactionAlreadyStarted()
    
    def add_file(self, file: 'FVSFile'):
        """
        This method add a file to the catalog and append it to the
        transaction list. Files already in the catalog will be updated 
        listing the new state for the deduplication. A FVSFile object
        is needed for the 'file' parameter.
        ...
        Raises:
            FVSStateDataHasNoState: if the state is not set.
        """
        if not self.__state:
            raise FVSStateDataHasNoState()
        
        self.__set_transaction_type(0)
        
        if file.md5 not in self.__data_conf.keys():
            logger.debug(f"Adding file {file.file_name} to data catalog.")
            self.__data_conf[file.md5] = {
                "file_name": file.file_name,
                "md5": file.md5,
                "states": [self.__state.state_id],
            }
            self.__transaction.append(file)

        elif self.__state.state_id not in self.__data_conf[file.md5]["states"]:
            logger.debug(f"Adding state {self.__state.state_id} to file {file.file_name} in data catalog.")
            self.__data_conf[file.md5]["states"].append(self.__state.state_id)
            self.__transaction.append(file)
            
        else:
            logger.debug(f"File {file.file_name} already in data catalog.")
    
    def delete_file(self, file: 'FVSFile', state_id: int=None):
        """
        This method delete a state for a file in the catalog, it will
        remove the file entry if the state is the last one. If state_id
        is not set, the one defined in the FVSFile object will be used, 
        assuming it was the intended state.
        ...
        Raises:
            FVSStateDataHasNoState: if the state is not set.
        """
        if state_id is None and not self.__state:
            raise FVSStateDataHasNoState()
        
        if state_id is None:
            state_id = self.__state.state_id
        
        self.__set_transaction_type(1)
            
        if file.md5 in self.__data_conf.keys():
            if state_id in self.__data_conf[file.md5]["states"]:
                logger.debug(f"Unlinking state {state_id} from file {file.file_name} in data catalog.")
                self.__data_conf[file.md5]["states"].remove(state_id)
                
                if len(self.__data_conf[file.md5]["states"]) == 0:
                    logger.debug(f"{state_id} was the last state for file {file.file_name}. Removing file from data catalog.")
                    del self.__data_conf[file.md5]
                    self.__transaction.append(file)
                
            else:
                logger.debug(f"File {file.file_name} has no state {self.__state.state_id}. Ignoring.")
        else:
            logger.debug(f"File {file.file_name} is not in data catalog. Ignoring.")
                