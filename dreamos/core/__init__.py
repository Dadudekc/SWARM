# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from importlib import import_module
from typing import Any
import sys as _sys

__all__ = [
    "agent_interface",
    "agent_loop",
    "cli",
    "config",
    "cursor_controller",
    "log_manager",
    "menu",
    "message",
    "persistent_queue",
    "response_collector_new",
    "start_dreamos",
    "system_init",
]

_prefix = __name__


def __getattr__(name: str) -> Any:  # noqa: D401
    if name not in __all__:
        raise AttributeError(name)
    try:
        module = import_module(f"{_prefix}.{name}")
    except ModuleNotFoundError:
        # Provide dummy fallback
        dummy = type(name, (), {"__getattr__": lambda *_: None})
        _sys.modules[f"{_prefix}.{name}"] = dummy  # type: ignore
        return dummy
    globals()[name] = module
    return module
