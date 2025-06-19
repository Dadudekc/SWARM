"""Minimal reimplementation of legacy file utility helpers required by tests.
This module purposefully implements **only** the subset of functionality
used by the test-suite.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Set, Tuple, Optional

__all__: list[str] = [
    "is_valid_file",
    "is_test_file",
    "get_file_extension",
    "normalize_path",
    "ensure_dir",
    "clean_dir",
    "safe_mkdir",
    "safe_rmdir",
    "read_file",
    "write_file",
    "read_json",
    "write_json",
    "read_yaml",
    "write_yaml",
    "backup_file",
    "archive_file",
    "extract_agent_id",
]

# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def _to_path(p: os.PathLike | str | Path) -> Path:  # noqa: D401
    """Convert arbitrary path-like to ``Path`` instance."""
    return p if isinstance(p, Path) else Path(p)


def get_file_extension(path: Path) -> str:  # noqa: D401
    return path.suffix


def is_valid_file(path: os.PathLike | str | Path, valid_extensions: Set[str]) -> bool:  # noqa: D401
    """Lightweight file validation used in tests.

    Criteria (as reflected in *tests/unit/utils/test_file_utils.py*):
    1. The suffix must be one of the allowed ``valid_extensions``.
    2. The filename must **not** contain wildcard characters (``*``).
    3. The path must **not** be inside a ``__pycache__`` directory.

    **Notably**, *file existence is *not* checked* – the tests pass hypothetical
    paths (e.g. ``temp_dir / 'test.py'``) that may not have been created yet.
    """
    p = _to_path(path)
    if p.suffix not in valid_extensions:
        return False
    if "*" in p.name:
        return False
    if "__pycache__" in p.parts:
        return False
    return True


def is_test_file(path: os.PathLike | str | Path) -> bool:  # noqa: D401
    p = _to_path(path)
    return "test" in p.name or p.parent.name == "tests"


def normalize_path(path: Path) -> Path:  # noqa: D401
    """Normalize paths according to test expectations.

    * Absolute paths are resolved.
    * Relative paths are returned unchanged.
    * Any path containing wildcard characters raises ``ValueError``.
    """
    if "*" in path.name:
        raise ValueError("Wildcard characters not allowed in path")
    return path.resolve() if path.is_absolute() else path


def ensure_dir(path: os.PathLike | str | Path) -> None:  # noqa: D401
    _to_path(path).mkdir(parents=True, exist_ok=True)


def clean_dir(path: os.PathLike | str | Path) -> None:  # noqa: D401
    p = _to_path(path)
    if not p.exists():
        return
    for child in p.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink(missing_ok=True)
        else:
            shutil.rmtree(child, ignore_errors=True)


def safe_mkdir(path: os.PathLike | str | Path) -> None:  # noqa: D401
    ensure_dir(path)


def safe_rmdir(path: os.PathLike | str | Path) -> None:  # noqa: D401
    p = _to_path(path)
    shutil.rmtree(p, ignore_errors=True)

# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def read_file(path: os.PathLike | str | Path) -> str:  # noqa: D401
    with open(_to_path(path), "r", encoding="utf-8") as fp:
        return fp.read()


def write_file(path: os.PathLike | str | Path, content: str) -> None:  # noqa: D401
    ensure_dir(_to_path(path).parent)
    with open(_to_path(path), "w", encoding="utf-8") as fp:
        fp.write(content)


def read_json(path: os.PathLike | str | Path) -> Dict[str, Any]:  # noqa: D401
    with open(_to_path(path), "r", encoding="utf-8") as fp:
        return json.load(fp)


def write_json(path: os.PathLike | str | Path, data: Dict[str, Any]) -> None:  # noqa: D401
    ensure_dir(_to_path(path).parent)
    with open(_to_path(path), "w", encoding="utf-8") as fp:
        json.dump(data, fp)

# YAML operations require PyYAML. Provide fallback no-op if absent.
try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def read_yaml(path: os.PathLike | str | Path):  # noqa: D401
    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    with open(_to_path(path), "r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def write_yaml(path: os.PathLike | str | Path, data) -> None:  # noqa: D401
    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    ensure_dir(_to_path(path).parent)
    with open(_to_path(path), "w", encoding="utf-8") as fp:
        yaml.safe_dump(data, fp)

# ---------------------------------------------------------------------------
# Backup / archive helpers
# ---------------------------------------------------------------------------

def _make_suffix(path: Path, suffix: str) -> Path:  # noqa: D401
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")


def backup_file(path: os.PathLike | str | Path) -> Path:  # noqa: D401
    p = _to_path(path)
    backup = _make_suffix(p, "_bak")
    ensure_dir(backup.parent)
    shutil.copy2(p, backup)
    return backup


def archive_file(path: os.PathLike | str | Path) -> Path:  # noqa: D401
    p = _to_path(path)
    archive = _make_suffix(p, "_archive")
    ensure_dir(archive.parent)
    shutil.move(p, archive)
    return archive


def extract_agent_id(path: Path) -> Optional[str]:  # noqa: D401
    for part in path.parts:
        if part.startswith("agent_"):
            suffix = part.removeprefix("agent_")
            if suffix.isdigit():
                return suffix
    return None 