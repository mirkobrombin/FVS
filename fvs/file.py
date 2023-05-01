import os
import shutil
import tarfile
import logging

logger = logging.getLogger("fvs.file")


# noinspection DuplicatedCode
class FVSFile:

    def __init__(self, repo: 'FVSRepo', file_name: str, sha1: str, relative_paths: list):
        self.__repo = repo
        self.__file_name = file_name
        self.__sha1 = sha1
        self.__relative_paths = relative_paths

    def is_equal(self, file: 'FVSFile') -> bool:
        return self.__sha1 == file.get_sha1()

    def as_dict(self) -> dict:
        return {
            "file_name": self.__file_name,
            "sha1": self.__sha1,
            "relative_paths": self.__relative_paths
        }

    def copy_to(self, dest: str, use_sha1_as_name: bool = True):
        """
        This method copy the file to the given destination. Despite it looks 
        flexible, it is meant to be used only by FVSData to copy files to 
        the appropriate data location, for this reason use_sha1_as_name is 
        set to True by default (data files must be stored with their sha1 
        hash as name to avoid name collisions). This method use copy2 to
        copy the file, so it will preserve the file metadata.
        """

        if self.__repo.has_compression:
            self.__compress_copy_to(dest, use_sha1_as_name)
            return

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

        """
        We will move only the first relative path as the file is supposed to
        be the same in all relative paths.
        """
        logger.debug(f"Copying file {_name} to {dest}")
        shutil.copy2(
            os.path.join(self.__repo.repo_path, self.__relative_paths[0]),
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
        if self.__repo.has_compression:
            self.__compress_restore(internal_path)
            return
            
        file_path = os.path.join(internal_path, self.__sha1)
        if not os.path.exists(file_path):
            logger.debug(f"file {self.__file_name} does not exist, data catalog may be corrupted.")
            return

        for relative_path in self.__relative_paths:
            dir_name = os.path.dirname(os.path.join(self.__repo.repo_path, relative_path))
            logger.debug(f"restoring file {self.__file_name}")
            os.makedirs(dir_name, exist_ok=True)
            shutil.copy2(
                file_path,
                os.path.join(self.__repo.repo_path, relative_path),
                follow_symlinks=False
            )
    
    def __compress_copy_to(self, dest: str, use_sha1_as_name: bool = True):
        """
        This method will copy the file to the given destination, compressing it.
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

        """
        We will move only the first relative path as the file is supposed to
        be the same in all relative paths.
        """
        logger.debug(f"Compressing file {_name} to {dest}")
        with tarfile.open(_dest, "w:gz") as tar:
            tar.add(
                os.path.join(self.__repo.repo_path, self.__relative_paths[0]),
                arcname=_name
            )
    
    def __compress_restore(self, internal_path: str):
        """
        This method will restore the file, decompressing it and copying it
        to the repo.
        """
        file_path = os.path.join(internal_path, self.__sha1)
        if not os.path.exists(file_path):
            logger.debug(f"file {self.__file_name} does not exist, data catalog may be corrupted.")
            return

        for relative_path in self.__relative_paths:
            full_rel_path = os.path.join(self.__repo.repo_path, relative_path)
            dir_name = os.path.dirname(full_rel_path)
            logger.debug(f"restoring file {self.__file_name}")
            os.makedirs(dir_name, exist_ok=True)
            with tarfile.open(file_path, "r:gz") as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, dir_name)
                os.rename(
                    os.path.join(dir_name, self.__sha1),
                    full_rel_path
                )

    @property
    def file_name(self) -> str:
        return self.__file_name

    @property
    def sha1(self) -> str:
        return self.__sha1

    @property
    def relative_paths(self) -> list:
        return self.__relative_paths
