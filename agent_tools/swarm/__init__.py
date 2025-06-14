"""agent_tools.swarm – legacy shim."""
from __future__ import annotations

from importlib import import_module as _import_module
import sys as _sys

# Re-export analyzers
_analyzers = _import_module(__name__ + '.analyzers')
_sys.modules[__name__ + '.analyzers'] = _analyzers

__all__ = ["analyzers"] 