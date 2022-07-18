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
    def get_md5_hash(path: str, block_size: int = 2 ** 20):
        md5_temp = hashlib.md5()
        with open(path, "rb") as f:
            while True:
                buffer = f.read(block_size)
                if not buffer:
                    break
                md5_temp.update(buffer)
        return md5_temp.hexdigest()
