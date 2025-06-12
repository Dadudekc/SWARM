"""Unified validation system for Dream.OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

from ...utils.metrics import metrics, logger, log_operation
from ...utils.exceptions import handle_error

T = TypeVar('T')

class ValidationError(Exception):
    """Base exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            code: Error code
            details: Additional error details
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()
        
        # Log error
        logger.error(
            "validation_error",
            extra={
                "code": code,
                "message": message,
                "details": details
            }
        )
        
        # Record metric
        metrics.counter(
            "validation_errors_total",
            "Total validation errors",
            ["code"]
        ).labels(code=code).inc()

class ValidationResult(Generic[T]):
    """Result of a validation operation."""
    
    def __init__(
        self,
        is_valid: bool,
        data: Optional[T] = None,
        errors: Optional[List[ValidationError]] = None
    ):
        """Initialize validation result.
        
        Args:
            is_valid: Whether validation passed
            data: Validated data
            errors: List of validation errors
        """
        self.is_valid = is_valid
        self.data = data
        self.errors = errors or []
        self.timestamp = datetime.now()

class BaseValidator(ABC, Generic[T]):
    """Base class for all validators in Dream.OS."""
    
    def __init__(self, name: str):
        """Initialize the validator.
        
        Args:
            name: Name of the validator
        """
        self.name = name
        self._metrics = {
            'validations': metrics.counter(
                'validator_validations_total',
                'Total validations',
                ['validator', 'result']
            ),
            'errors': metrics.counter(
                'validator_errors_total',
                'Total validation errors',
                ['validator', 'error_type']
            ),
            'duration': metrics.histogram(
                'validator_duration_seconds',
                'Validation duration',
                ['validator']
            )
        }
    
    @abstractmethod
    def validate(self, data: Any) -> ValidationResult[T]:
        """Validate the given data.
        
        Args:
            data: The data to validate
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def add_error(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> ValidationError:
        """Add a validation error.
        
        Args:
            message: Error message
            code: Error code
            details: Additional error details
            
        Returns:
            Created ValidationError
        """
        error = ValidationError(message, code, details)
        self._metrics['errors'].labels(
            validator=self.name,
            error_type=error.__class__.__name__
        ).inc()
        return error
    
    @log_operation('validator_validate', metrics='validations', duration='duration')
    def validate_with_metrics(self, data: Any) -> ValidationResult[T]:
        """Validate data with metrics tracking.
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        try:
            result = self.validate(data)
            
            # Record metrics
            self._metrics['validations'].labels(
                validator=self.name,
                result="success" if result.is_valid else "failure"
            ).inc()
            
            return result
            
        except Exception as e:
            error = handle_error(e, {
                "validator": self.name,
                "operation": "validate"
            })
            
            # Record error metric
            self._metrics['errors'].labels(
                validator=self.name,
                error_type=error.__class__.__name__
            ).inc()
            
            # Create validation result with error
            return ValidationResult(
                is_valid=False,
                errors=[self.add_error(str(error), "VALIDATION_ERROR", {"error": error})]
            )

class SchemaValidator(BaseValidator[T]):
    """Validator that uses a schema for validation."""
    
    def __init__(
        self,
        name: str,
        schema: Dict[str, Any],
        data_type: Type[T]
    ):
        """Initialize schema validator.
        
        Args:
            name: Name of the validator
            schema: Validation schema
            data_type: Type of data being validated
        """
        super().__init__(name)
        self.schema = schema
        self.data_type = data_type
    
    def validate(self, data: Any) -> ValidationResult[T]:
        """Validate data against schema.
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        errors: List[ValidationError] = []
        
        # Check required fields
        required_fields = self.schema.get('required', [])
        for field in required_fields:
            if field not in data:
                errors.append(self.add_error(
                    f"Missing required field: {field}",
                    "MISSING_REQUIRED_FIELD",
                    {"field": field}
                ))
        
        # Check field types
        properties = self.schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in data:
                field_type = field_schema.get('type')
                if field_type and not isinstance(data[field], self._get_type(field_type)):
                    errors.append(self.add_error(
                        f"Invalid type for field {field}: expected {field_type}",
                        "INVALID_FIELD_TYPE",
                        {
                            "field": field,
                            "expected_type": field_type,
                            "actual_type": type(data[field]).__name__
                        }
                    ))
        
        # Check field values
        for field, field_schema in properties.items():
            if field in data:
                # Check minimum/maximum
                if 'minimum' in field_schema and data[field] < field_schema['minimum']:
                    errors.append(self.add_error(
                        f"Field {field} below minimum value",
                        "BELOW_MINIMUM",
                        {
                            "field": field,
                            "minimum": field_schema['minimum'],
                            "value": data[field]
                        }
                    ))
                if 'maximum' in field_schema and data[field] > field_schema['maximum']:
                    errors.append(self.add_error(
                        f"Field {field} above maximum value",
                        "ABOVE_MAXIMUM",
                        {
                            "field": field,
                            "maximum": field_schema['maximum'],
                            "value": data[field]
                        }
                    ))
                
                # Check pattern
                if 'pattern' in field_schema:
                    import re
                    if not re.match(field_schema['pattern'], str(data[field])):
                        errors.append(self.add_error(
                            f"Field {field} does not match pattern",
                            "PATTERN_MISMATCH",
                            {
                                "field": field,
                                "pattern": field_schema['pattern'],
                                "value": data[field]
                            }
                        ))
        
        # Convert data to expected type if valid
        if not errors:
            try:
                converted_data = self.data_type(**data)
                return ValidationResult(is_valid=True, data=converted_data)
            except Exception as e:
                error = handle_error(e, {
                    "validator": self.name,
                    "operation": "convert",
                    "data": data
                })
                errors.append(self.add_error(
                    f"Failed to convert data to {self.data_type.__name__}",
                    "CONVERSION_ERROR",
                    {"error": str(error)}
                ))
        
        return ValidationResult(is_valid=False, errors=errors)
    
    def _get_type(self, type_name: str) -> Type:
        """Get Python type from schema type name.
        
        Args:
            type_name: Schema type name
            
        Returns:
            Python type
        """
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        return type_map.get(type_name, Any) 