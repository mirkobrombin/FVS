import fnmatch
import logging

logger = logging.getLogger("fvs.pattern")


class FVSPattern:

    @staticmethod
    def match(patterns: list, file_name: str):
        """
        This method will check if the file_name matches the pattern. It is
        currently just a wrapper around fnmatch.fnmatch. Here just for better
        code readability and future improvements.
        """
        for pattern in patterns:
            if fnmatch.fnmatch(file_name, pattern):
                logger.debug(f"One pattern match: {file_name} matches {pattern}")
                return True
        return False
