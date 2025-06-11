"""
Base validation functionality for Dream.OS.
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Base exception for validation errors."""
    pass

class BaseValidator:
    """Base class for all validators in Dream.OS."""
    
    def __init__(self):
        self.errors: List[str] = []
        
    def validate(self, data: Any) -> bool:
        """
        Validate the given data.
        
        Args:
            data: The data to validate
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")
        
    def add_error(self, message: str) -> None:
        """
        Add an error message to the validator.
        
        Args:
            message: The error message to add
        """
        self.errors.append(message)
        logger.error(f"Validation error: {message}")
        
    def get_errors(self) -> List[str]:
        """
        Get all validation errors.
        
        Returns:
            List[str]: List of error messages
        """
        return self.errors
        
    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.errors = []
        
    def has_errors(self) -> bool:
        """
        Check if there are any validation errors.
        
        Returns:
            bool: True if there are errors, False otherwise
        """
        return len(self.errors) > 0 