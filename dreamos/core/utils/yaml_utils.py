"""YAML utilities for Dream.OS."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union, Dict, Optional, Type, TypeVar

import yaml
from cerberus import Validator

from ..shared.validation.base import BaseValidator, ValidationResult, SchemaValidator
from .metrics import metrics, logger, log_operation
from .exceptions import handle_error

T = TypeVar('T')

logger = logging.getLogger(__name__)

__all__ = [
    "load_yaml",
    "save_yaml",
    "read_yaml",
    "write_yaml",
    "validate_yaml",
    "YamlError",
]


class YamlError(Exception):
    """Exception raised for YAML-related errors."""
    pass


def read_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML data from file."""
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error reading YAML from {file_path}: {e}")
        return default


def load_yaml(
    file_path: Path,
    schema: Optional[Dict[str, Any]] = None,
    data_type: Optional[Type[T]] = None
) -> Optional[T]:
    """Load and validate YAML file.
    
    Args:
        file_path: Path to YAML file
        schema: Optional validation schema
        data_type: Optional type of data being loaded
        
    Returns:
        Loaded and validated data, or None if validation fails
    """
    try:
        # Read YAML file
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Validate if schema and type provided
        if schema and data_type:
            result = validate_yaml(file_path, schema, data_type)
            if not result.is_valid:
                logger.error(
                    "yaml_validation_failed",
                    extra={
                        "file": str(file_path),
                        "errors": [str(e) for e in result.errors]
                    }
                )
                return None
            return result.data
        
        return data
        
    except Exception as e:
        error = handle_error(e, {
            "operation": "load_yaml",
            "file": str(file_path)
        })
        logger.error(
            "yaml_load_failed",
            extra={
                "file": str(file_path),
                "error": str(error)
            }
        )
        return None


def write_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Write data to YAML file."""
    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error writing YAML to {file_path}: {e}")
        return False


def save_yaml(
    file_path: Path,
    data: Any,
    schema: Optional[Dict[str, Any]] = None,
    data_type: Optional[Type[T]] = None
) -> bool:
    """Save data to YAML file with optional validation.
    
    Args:
        file_path: Path to YAML file
        data: Data to save
        schema: Optional validation schema
        data_type: Optional type of data being saved
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate if schema and type provided
        if schema and data_type:
            validator = YAMLValidator(
                "yaml_validator",
                schema,
                data_type
            )
            result = validator.validate(data)
            if not result.is_valid:
                logger.error(
                    "yaml_validation_failed",
                    extra={
                        "file": str(file_path),
                        "errors": [str(e) for e in result.errors]
                    }
                )
                return False
        
        # Save YAML file
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f)
        
        return True
        
    except Exception as e:
        error = handle_error(e, {
            "operation": "save_yaml",
            "file": str(file_path)
        })
        logger.error(
            "yaml_save_failed",
            extra={
                "file": str(file_path),
                "error": str(error)
            }
        )
        return False


class YAMLValidator(BaseValidator[T]):
    """Validator for YAML files."""
    
    def __init__(
        self,
        name: str,
        schema: Dict[str, Any],
        data_type: Type[T]
    ):
        """Initialize YAML validator.
        
        Args:
            name: Name of the validator
            schema: Validation schema
            data_type: Type of data being validated
        """
        super().__init__(name)
        self.schema_validator = SchemaValidator(
            f"{name}_schema",
            schema,
            data_type
        )
    
    @log_operation('yaml_validate', metrics='validations', duration='duration')
    def validate_file(self, file_path: Path) -> ValidationResult[T]:
        """Validate YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        try:
            # Read YAML file
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate data
            return self.validate(data)
            
        except yaml.YAMLError as e:
            error = handle_error(e, {
                "validator": self.name,
                "operation": "parse_yaml",
                "file": str(file_path)
            })
            return ValidationResult(
                is_valid=False,
                errors=[self.add_error(
                    f"Failed to parse YAML file: {str(error)}",
                    "YAML_PARSE_ERROR",
                    {"file": str(file_path), "error": str(error)}
                )]
            )
        except Exception as e:
            error = handle_error(e, {
                "validator": self.name,
                "operation": "validate_file",
                "file": str(file_path)
            })
            return ValidationResult(
                is_valid=False,
                errors=[self.add_error(
                    f"Failed to validate YAML file: {str(error)}",
                    "VALIDATION_ERROR",
                    {"file": str(file_path), "error": str(error)}
                )]
            )
    
    def validate(self, data: Any) -> ValidationResult[T]:
        """Validate YAML data.
        
        Args:
            data: YAML data to validate
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        return self.schema_validator.validate(data)


def validate_yaml(
    file_path: Path,
    schema: Dict[str, Any],
    data_type: Type[T]
) -> ValidationResult[T]:
    """Validate YAML file against schema.
    
    Args:
        file_path: Path to YAML file
        schema: Validation schema
        data_type: Type of data being validated
        
    Returns:
        ValidationResult containing validation status and any errors
    """
    validator = YAMLValidator(
        "yaml_validator",
        schema,
        data_type
    )
    return validator.validate_file(file_path) 