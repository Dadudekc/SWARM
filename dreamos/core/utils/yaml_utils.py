"""YAML serialization and deserialization utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union, Dict

import yaml
from cerberus import Validator

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


def load_yaml(file_path: Union[str, Path], default: Any = None) -> Any:
    """Alias for read_yaml for backward compatibility."""
    return read_yaml(file_path, default)


def write_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Write data to YAML file."""
    try:
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
        return True
    except Exception as e:  # pragma: no cover - simple log
        logger.error(f"Error writing YAML to {file_path}: {e}")
        return False


def save_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """Save data to YAML file."""
    return write_yaml(file_path, data)


def validate_yaml(data: Dict, schema: Dict) -> tuple[bool, Dict]:
    """Validate YAML data against a schema.
    
    Args:
        data: YAML data to validate
        schema: Cerberus validation schema
        
    Returns:
        Tuple of (is_valid, errors)
    """
    try:
        validator = Validator(schema)
        is_valid = validator.validate(data)
        return is_valid, validator.errors
    except Exception as e:
        logger.error(f"Error validating YAML: {e}")
        return False, {"validation_error": str(e)} 
