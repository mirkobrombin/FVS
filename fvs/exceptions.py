class FVSException(Exception):
    """
    Base class for all FVS exceptions.
    """

    def __init__(self, message: str = "An unknown error occurred."):
        super().__init__(message)


class FVSStateNotFound(FVSException):
    """
    Exception raised when a state is not found.
    """

    def __init__(self, state_id: int):
        super().__init__("No state found for ID: {}".format(state_id))


class FVSEmptyStateIndex(FVSException):
    """
    Exception raised when the state index is empty.
    """

    def __init__(self, state_id: int):
        super().__init__("Index is empty for state ID: {}".format(state_id))


class FVSMissingStateIndex(FVSException):
    """
    Exception raised when a state index is not found.
    """

    def __init__(self, state_id: int):
        super().__init__("State index not found for state with ID: {}".format(state_id))


class FVSFileNotFound(FVSException):
    """
    Exception raised when a file is not found.
    """

    def __init__(self):
        super().__init__("File not found in the state.")


class FVSFileAlreadyExists(FVSException):
    """
    Exception raised when a file already exists.
    """

    def __init__(self):
        super().__init__("File already exists.")


class FVSNothingToCommit(FVSException):
    """
    Exception raised when there is nothing to commit.
    """

    def __init__(self):
        super().__init__("Nothing to commit.")


class FVSEmptyCommitMessage(FVSException):
    """
    Exception raised when the commit message is empty.
    """

    def __init__(self):
        super().__init__("Commit message is empty.")


class FVSCallerWrongClass(FVSException):
    """
    Exception raised when the caller is not the expected class.
    """

    def __init__(self, cls: str = "FVSRepo"):
        super().__init__("Caller is not the expected class: {}".format(cls))


class FVSWrongUnstagedDict(FVSException):
    """
    Exception raised when the unstaged_files dict is not correct.
    """

    def __init__(self):
        super().__init__("The unstaged_files dict is not correct (following\
keys are required: added, modified, removed, intact).")


class FVSUnsupportedKey(FVSException):
    """
    Exception raised when the has_relative_path method was requested
    with a wrong key.
    """

    def __init__(self, supported_keys: list):
        super().__init__("The has_relative_path method was requested with a \
wrong key, the following are corrected: {}.".format(supported_keys))


class FVSCommittingToExistingState(FVSException):
    """
    Exception raised when committing to an existing state.
    """

    def __init__(self):
        super().__init__("You were trying to commit to an existing state. \
This is not allowed and states are not meant to be altered \
once the first commit has been made.")


class FVSDataHasNoState(FVSException):
    """
    Exception raised when the state data has no state.
    """

    def __init__(self):
        super().__init__("FVSData was initialized without a FVSState, \
but a FVSState was expected to perform transactions.")


class VFSTransactionAlreadyStarted(FVSException):
    """
    Exception raised when a transaction is already started.
    """

    def __init__(self):
        super().__init__("A different kind of transaction is already started.")


class FVSWrongSortBy(FVSException):
    """
    Exception raised when a sort_by parameter is not correct.
    """

    def __init__(self, allowed_sort_by: list):
        super().__init__("The sort_by parameter is not correct. \
It should be one of the following: {}".format(allowed_sort_by))


class FVSNothingToRestore(FVSException):
    """
    Exception raised when there is nothing to restore.
    """

    def __init__(self):
        super().__init__("Nothing to restore.")


class FVSStateZeroNotDeletable(FVSException):
    """
    Exception raised when a state with ID 0 is not deletable.
    """

    def __init__(self):
        super().__init__("State with ID 0 is not deletable.")


class FVSStateAlreadyExists(FVSException):
    """
    Exception raised when a state already exists.
    """

    def __init__(self, state_id: int):
        super().__init__("State already exists with ID: {}".format(state_id))
