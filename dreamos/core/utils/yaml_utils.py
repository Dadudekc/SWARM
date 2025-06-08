"""YAML serialization and deserialization utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union

import yaml

logger = logging.getLogger(__name__)

__all__ = [
    "load_yaml",
    "save_yaml",
    "read_yaml",
    "write_yaml",
]


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