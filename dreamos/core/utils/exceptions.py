"""Custom exceptions for file operations."""


class FileOpsError(Exception):
    """Base exception for file operations."""


class FileOpsPermissionError(FileOpsError):
    """Raised when a file operation fails due to permission issues."""


class FileOpsIOError(FileOpsError):
    """Raised when a file operation fails due to I/O errors."""
