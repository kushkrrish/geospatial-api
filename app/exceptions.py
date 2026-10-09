class PermanentProcessingError(Exception):
    """Raised when the file is invalid and should NEVER be retried."""
    pass

class InvalidKMLError(PermanentProcessingError):
    pass

class InvalidFileError(PermanentProcessingError):
    pass