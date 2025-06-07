"""Validation Engine
----------------
Validates responses and ensures they meet required criteria.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ValidationEngine:
    """Engine for validating responses."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validation engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.validators: List[callable] = []
        
    def add_validator(self, validator: callable):
        """Add a validator function.
        
        Args:
            validator: Function that takes a response and returns a ValidationResult
        """
        self.validators.append(validator)
        
    def validate(self, response: Dict[str, Any]) -> ValidationResult:
        """Validate a response.
        
        Args:
            response: The response to validate
            
        Returns:
            ValidationResult containing validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        for validator in self.validators:
            try:
                result = validator(response)
                if not result.is_valid:
                    errors.extend(result.errors)
                warnings.extend(result.warnings)
            except Exception as e:
                logger.error(f"Validator error: {e}")
                errors.append(f"Validator failed: {str(e)}")
                
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def validate_required_fields(self, response: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """Validate that required fields are present.
        
        Args:
            response: The response to validate
            required_fields: List of required field names
            
        Returns:
            ValidationResult
        """
        errors = []
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
                
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
        
    def validate_field_type(self, response: Dict[str, Any], field: str, expected_type: type) -> ValidationResult:
        """Validate that a field has the expected type.
        
        Args:
            response: The response to validate
            field: Name of the field to check
            expected_type: Expected type of the field
            
        Returns:
            ValidationResult
        """
        if field not in response:
            return ValidationResult(
                is_valid=False,
                errors=[f"Missing field: {field}"],
                warnings=[]
            )
            
        if not isinstance(response[field], expected_type):
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field} has type {type(response[field])}, expected {expected_type}"],
                warnings=[]
            )
            
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        ) 