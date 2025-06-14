# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from importlib import import_module
from types import ModuleType
from typing import Any
import sys as _sys

__all__ = [
    "bridge",
    "start_dreamos",
]

# _lazy_targets maps public attribute names to their fully-qualified module.
_lazy_targets = {
    "bridge": "dreamos.bridge",
    "start_dreamos": "dreamos.start_dreamos",
}


def __getattr__(name: str) -> Any:  # noqa: D401, ANN001
    """Lazily import heavy sub-modules on first attribute access."""
    target = _lazy_targets.get(name)
    if target is None:  # pragma: no cover – unknown attribute
        raise AttributeError(name)

    module: ModuleType = import_module(target)
    _sys.modules[f"{__name__}.{name}"] = module  # cache for next time
    globals()[name] = module  # expose at package level
    return module
