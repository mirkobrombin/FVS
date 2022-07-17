import inspect
import hashlib


class FVSUtils:

    @staticmethod
    def get_caller_class_name():
        """
        Get the name of the caller class.
        """
        stack = inspect.stack()[2]
        caller = stack[0].f_locals.get('self').__class__.__name__
        return caller

    @staticmethod
    def get_md5_hash(path: str):
        """
        Get the MD5 hash of a file.
        """
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
