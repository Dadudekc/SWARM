# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from importlib import import_module
from types import ModuleType
from typing import Any
import sys as _sys

__all__ = [
    "agent_loop",
    "agent_state",
    "auto_trigger_runner",
    "autonomy_loop",
    "autonomy_loop_runner",
    "base_tracker",
    "bridge_writer",
    "codex_patch_tracker",
    "content_loop",
    "controller",
    "core_response_loop_daemon",
    "core_response_processor",
    "cursor_agent_bridge",
    "enhanced_response_loop_daemon",
    "error_tracking",
    "midnight_runner",
    "patch_validator",
    "processor_mode",
    "startup",
    "state",
    "test_watcher",
    "validation_engine",
]

_prefix = __name__  # "dreamos.core.autonomy"


def __getattr__(name: str) -> Any:  # noqa: D401
    if name not in __all__:
        raise AttributeError(name)

    module: ModuleType = import_module(f"{_prefix}.{name}")
    _sys.modules[f"{__name__}.{name}"] = module  # cache
    globals()[name] = module
    return module
