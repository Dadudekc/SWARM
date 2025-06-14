"""agent_tools.swarm.analyzers – legacy analyzers package shim."""
from __future__ import annotations

import sys as _sys
from importlib import import_module as _import_module

__all__: list[str] = [
    "code_analyzer",
    "ast_analyzer",
    "duplicate_analyzer",
    "quality_analyzer",
    "architectural_analyzer",
]

for _sub in __all__:
    try:
        _mod = _import_module(f"{__name__}.{_sub}")
    except ModuleNotFoundError:  # pragma: no cover
        continue
    _sys.modules[f"{__name__}.{_sub}"] = _mod
    setattr(_sys.modules[__name__], _sub, _mod) 