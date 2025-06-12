"""Standardized error handling for Dream.OS."""

from __future__ import annotations

from typing import Optional, Dict, Any
from dreamos.core.utils.metrics import logger, metrics

class DreamOSError(Exception):
    """Base exception class for Dream.OS."""
    
    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize error.
        
        Args:
            message: Error message
            code: Error code
            details: Optional error details
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}
        
        # Log error
        logger.error(
            f"Error {code}: {message}",
            extra={
                "error_code": code,
                "error_details": self.details
            }
        )
        
        # Record metric
        metrics.counter(
            "errors_total",
            "Total errors",
            ["code"]
        ).labels(code=code).inc()

class FileOpsError(DreamOSError):
    """File operations error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize file operations error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "FILE_OPS_ERROR", details)

class FileOpsPermissionError(FileOpsError):
    """File permission error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize file permission error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "FILE_PERMISSION_ERROR", details)

class FileOpsIOError(FileOpsError):
    """File I/O error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize file I/O error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "FILE_IO_ERROR", details)

class ConfigError(DreamOSError):
    """Configuration error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize configuration error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "CONFIG_ERROR", details)

class MessageError(DreamOSError):
    """Message processing error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize message error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "MESSAGE_ERROR", details)

class ValidationError(DreamOSError):
    """Data validation error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "VALIDATION_ERROR", details)

class ResourceError(DreamOSError):
    """Resource management error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize resource error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "RESOURCE_ERROR", details)

class TimeoutError(DreamOSError):
    """Operation timeout error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize timeout error.
        
        Args:
            message: Error message
            details: Optional error details
        """
        super().__init__(message, "TIMEOUT_ERROR", details)

def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> DreamOSError:
    """Convert exception to Dream.OS error.
    
    Args:
        error: Original exception
        context: Optional error context
        
    Returns:
        DreamOSError: Standardized error
    """
    if isinstance(error, DreamOSError):
        return error
        
    # Convert common exceptions
    if isinstance(error, PermissionError):
        return FileOpsPermissionError(str(error), context)
    if isinstance(error, IOError):
        return FileOpsIOError(str(error), context)
    if isinstance(error, TimeoutError):
        return TimeoutError(str(error), context)
        
    # Default to generic error
    return DreamOSError(
        str(error),
        "UNKNOWN_ERROR",
        context
    )
