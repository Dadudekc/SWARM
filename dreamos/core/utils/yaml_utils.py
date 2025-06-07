import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .file_utils import (
    safe_read,
    safe_write,
    FileOpsError,
    FileOpsIOError,
    FileOpsPermissionError,
)


def load_yaml(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load YAML from file."""
    content = safe_read(file_path)
    if content is None:
        return None
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to parse YAML from {file_path}: {e}")
        return None


def save_yaml(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """Save data as YAML."""
    try:
        content = yaml.dump(data, default_flow_style=False)
        return safe_write(file_path, content)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to save YAML to {file_path}: {e}")
        return False


def read_yaml(path: Union[str, Path], default: Any = None) -> Any:
    """Read YAML from a file with fallback options."""
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise FileOpsError(f"File not found: {path}")

    try:
        with open(path) as f:
            content = f.read()
            if not content.strip():
                return default if default is not None else {}
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                try:
                    yaml.scanner.Scanner(content)
                    yaml.parser.Parser(content)
                except Exception as e2:
                    if default is not None:
                        return default
                    raise FileOpsIOError(f"Invalid YAML in {path}: {e2}")
                return yaml.safe_load(content)
    except Exception as e:
        if default is not None:
            return default
        raise FileOpsIOError(f"Error reading YAML from {path}: {e}")


def write_yaml(path: Union[str, Path], data: dict) -> None:
    """Write YAML to a file."""
    try:
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except PermissionError as e:
        raise FileOpsPermissionError(f"Permission denied: {path}") from e
    except IOError as e:
        raise FileOpsIOError(f"I/O error: {path}") from e

