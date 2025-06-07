import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .file_utils import safe_read, safe_write, FileOpsError, FileOpsIOError


def load_json(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load JSON from file."""
    content = safe_read(file_path)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Reuse logger from file_utils for consistency
        import logging
        logging.getLogger(__name__).error(f"Failed to parse JSON from {file_path}: {e}")
        return None


def save_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """Save data as JSON."""
    try:
        content = json.dumps(data, indent=indent)
        return safe_write(file_path, content)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to save JSON to {file_path}: {e}")
        return False


def read_json(path: Union[str, Path], default: Any = None) -> Dict[str, Any]:
    """Read JSON from a file with error handling."""
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise FileOpsError(f"File not found: {path}")

    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        if default is not None:
            return default
        raise FileOpsIOError(f"Invalid JSON in {path}: {e}")


def write_json(path: Union[str, Path], data: dict) -> None:
    """Write JSON to a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

