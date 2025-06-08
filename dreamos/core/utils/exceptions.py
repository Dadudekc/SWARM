"""Custom exceptions for file operations."""

from typing import Optional


class FileOpsError(Exception):
    """Base exception for file operations."""


class FileOpsPermissionError(FileOpsError):
    """Raised when a file operation fails due to permission issues."""


class FileOpsIOError(FileOpsError):
    """Raised when a file operation fails due to I/O errors."""


class DreamOSError(Exception):
    """Legacy Dream.OS error for compatibility."""


class BridgeError(Exception):
    """Base exception for bridge-related errors."""
    
    def __init__(self, message: str, error_code: Optional[int] = None):
        """Initialize the bridge error.
        
        Args:
            message: Error message
            error_code: Optional error code for programmatic handling
        """
        super().__init__(message)
        self.error_code = error_code
