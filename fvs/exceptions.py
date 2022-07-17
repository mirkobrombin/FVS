class FVSException(Exception):
    """
    Base class for all FVS exceptions.
    """
    
    def __init__(self, message="An unknown error occurred."):
        super().__init__(message)


class FVSStateNotFound(FVSException):
    """
    Exception raised when a state is not found.
    """
    
    def __init__(self, state_id:int):
        super().__init__("No state found for ID: {}".format(state_id))


class FVSEmptyStateIndex(FVSException):
    """
    Exception raised when the state index is empty.
    """
    
    def __init__(self, state_id:int):
        super().__init__("Index is empty for state ID: {}".format(state_id))


class FVSMissingStateIndex(FVSException):
    """
    Exception raised when a state index is not found.
    """
    
    def __init__(self, state_id:int):
        super().__init__("State index not found for state with ID: {}".format(state_id))


class FVSFileNotFound(FVSException):
    """
    Exception raised when a file is not found.
    """
    
    def __init__(self):
        super().__init__("File not found.")


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
    
    def __init__(self, cls="FVSRepo"):
        super().__init__("Caller is not the expected class: {}".format(cls))


class FVSWrongUnstagedDict(FVSException):
    """
    Exception raised when the unstaged_files dict is not correct.
    """
    
    def __init__(self):
        super().__init__("The unstaged_files dict is not correct (following\
keys are required: added, modified, removed).")


class FVSCommittingToExistingState(FVSException):
    """
    Exception raised when committing to an existing state.
    """
    
    def __init__(self):
        super().__init__("You were trying to commit to an existing state. \
This is not allowed and states are not meant to be altered \
once the first commit has been made.")


class FVSStateDataHasNoState(FVSException):
    """
    Exception raised when the state data has no state.
    """
    
    def __init__(self):
        super().__init__("FVSData was initialized without a FVSState, \
but a FVSState was expected to perform transactions.")
