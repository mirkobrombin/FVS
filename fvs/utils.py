import os
import inspect
import hashlib
from typing import Union


class FVSUtils:

    @staticmethod
    def get_caller_class_name() -> str:
        """
        Get the name of the caller class.
        """
        stack = inspect.stack()[2]
        caller = stack[0].f_locals.get('self').__class__.__name__
        return caller

    @staticmethod
    def get_sha1_hash(path: str, block_size: int = 2 ** 20) -> Union[str, None]:
        """
        Get the sha1 hash of the given file. It will use name+content
        to avoid empty files.
        """
        sha1_temp = hashlib.sha1()
        file_name = os.path.basename(path)
        try:
            with open(path, "rb") as f:
                while True:
                    buffer = f.read(block_size)
                    if not buffer:
                        break
                    sha1_temp.update(buffer)
            sha1_temp.update(file_name.encode())
            return sha1_temp.hexdigest()
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            return None
