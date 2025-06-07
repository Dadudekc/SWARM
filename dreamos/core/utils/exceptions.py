class FileOpsError(Exception):
    """Base exception for file operations."""
    pass

class FileOpsPermissionError(FileOpsError):
    """Raised when a file operation fails due to permission issues."""
    pass

class FileOpsIOError(FileOpsError):
    """Raised when a file operation fails due to I/O issues."""
    pass
