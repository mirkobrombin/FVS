import os
import shutil
import logging

logger = logging.getLogger("fvs.file")


# noinspection DuplicatedCode
class FVSFile:

    def __init__(self, repo: 'FVSRepo', file_name: str, sha1: str, relative_path: str):
        self.__repo = repo
        self.__file_name = file_name
        self.__sha1 = sha1
        self.__relative_path = relative_path

    def is_equal(self, file: 'FVSFile'):
        return self.__sha1 == file.get_sha1()

    def as_dict(self):
        return {
            "file_name": self.__file_name,
            "sha1": self.__sha1,
            "relative_path": self.__relative_path
        }

    def copy_to(self, dest: str, use_sha1_as_name: bool = True):
        """
        This method opy the file to the given destination. Despite it looks 
        flexible, it is meant to be used only by FVSData to copy files to 
        the appropriate data location, for this reason use_sha1_as_name is 
        set to True by default (data files must be stored with their sha1 
        hash as name to avoid name collisions). This method use copy2 to
        copy the file, so it will preserve the file metadata.
        """
        if use_sha1_as_name:
            _dest = os.path.join(dest, self.__sha1)
            _name = self.__sha1
        else:
            _dest = os.path.join(dest, self.__file_name)
            _name = self.__file_name

        """
        There never should be a file with the same name and FVSData should
        already check for duplicates. Anyway, we will check for it here
        just in case.
        """
        if os.path.islink(_dest) or os.path.exists(_dest):
            logger.debug(f"File {self.__sha1} already exists in {dest}.")
            return

        logger.debug(f"Copying file {_name} to {dest}")
        shutil.copy2(
            os.path.join(self.__repo.repo_path, self.__relative_path),
            _dest,
            follow_symlinks=False
        )

    def remove(self, path: str, use_sha1_as_name: bool = True):
        """
        This method will remove the file from the internal data directory.
        """
        if use_sha1_as_name:
            file_path = os.path.join(path, self.__sha1)
        else:
            file_path = os.path.join(path, self.__file_name)

        if os.path.exists(file_path):
            logger.debug(f"removing file {self.__file_name} from {path}")
            os.remove(file_path)
        else:
            logger.debug(f"file {self.__file_name} does not exist, data catalog may be corrupted.")

    def restore(self, internal_path: str):
        """
        This method will restore the file, copying from the internal data
        directory to the repo, renaming it to the original name.
        """
        file_path = os.path.join(internal_path, self.__sha1)
        dir_name = os.path.dirname(os.path.join(self.__repo.repo_path, self.__relative_path))

        if os.path.exists(file_path):
            logger.debug(f"restoring file {self.__file_name}")
            os.makedirs(dir_name, exist_ok=True)
            shutil.copy2(
                file_path,
                os.path.join(self.__repo.repo_path, self.__relative_path),
                follow_symlinks=False
            )
        else:
            logger.debug(f"file {self.__file_name} does not exist, data catalog may be corrupted.")

    @property
    def file_name(self):
        return self.__file_name

    @property
    def sha1(self):
        return self.__sha1

    @property
    def relative_path(self):
        return self.__relative_path
