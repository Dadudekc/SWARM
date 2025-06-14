"""Compatibility init for resumer_v2 package.

Ensures that the stub `AtomicFileManager` is eagerly imported so that
`import dreamos.core.resumer_v2.atomic_file_manager` works in legacy code.
"""
from __future__ import annotations

from .atomic_file_manager import AtomicFileManager  # noqa: F401

__all__: list[str] = [
    "AtomicFileManager",
]
