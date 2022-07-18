import fnmatch
import logging

logger = logging.getLogger("fvs.pattern")


class FVSPattern:

    @staticmethod
    def match(pattern: str, file_name: str):
        """
        This method will check if the file_name matches the pattern. It is
        currently just a wrapper around fnmatch.fnmatch. Here just for better
        code readability and future improvements.
        """
        res = fnmatch.fnmatch(file_name, pattern)
        logger.debug(f"Checking if {file_name} matches {pattern}: {res}")
        return res
