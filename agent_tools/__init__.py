"""Legacy agent_tools compatibility package."""

from __future__ import annotations

import sys
import types as _types

# ---------------------------------------------------------------------------
# Create sub-module hierarchy: agent_tools.mailbox.message_handler
# ---------------------------------------------------------------------------

_mailbox_mod = _types.ModuleType("agent_tools.mailbox")
_message_handler_mod = _types.ModuleType("agent_tools.mailbox.message_handler")

class MessageHandler:  # type: ignore
    """Stubbed MessageHandler – replace with real implementation if needed."""

    def __init__(self, *_, **__):
        pass

    # Legacy API methods (no-ops)
    def send_message(self, *_, **__):  # noqa: D401
        return True

    def broadcast_message(self, *_, **__):  # noqa: D401
        return True

    def get_messages(self, *_):  # noqa: D401
        return []

    def acknowledge_message(self, *_):  # noqa: D401
        return True


# Expose stub in module namespace
_message_handler_mod.MessageHandler = MessageHandler  # type: ignore[attr-defined]

# Register modules in sys.modules
sys.modules["agent_tools"] = sys.modules[__name__]
sys.modules["agent_tools.mailbox"] = _mailbox_mod
sys.modules["agent_tools.mailbox.message_handler"] = _message_handler_mod

# Make `mailbox` attribute accessible from top-level package
setattr(sys.modules[__name__], "mailbox", _mailbox_mod)
setattr(_mailbox_mod, "message_handler", _message_handler_mod)
setattr(_mailbox_mod, "MessageHandler", MessageHandler)

# ---------------------------------------------------------------------------
# If a *real* implementation of ``agent_tools.mailbox`` exists on disk, load
# it and replace the stub so callers (and tests) get the full API (enqueue /
# dequeue_all, etc.). This preserves backward-compatibility for legacy code
# paths that relied on the lightweight stub while enabling newer modules –
# like the onboarding helpers – to coexist without circular-import issues.
# ---------------------------------------------------------------------------

try:
    import importlib as _importlib

    _real_mailbox = _importlib.import_module("agent_tools.mailbox", package=__name__)

    # Heuristic: ensure the real module exposes at least one of the expected
    # public helpers (``enqueue``) before swapping out the stub. This prevents
    # unintentionally masking the stub with yet-to-be-initialized placeholder
    # modules in edge-cases (e.g. partially initialised during recursive
    # imports).
    if hasattr(_real_mailbox, "enqueue"):
        sys.modules["agent_tools.mailbox"] = _real_mailbox  # noqa: PLC0414 – intentional override
        setattr(sys.modules[__name__], "mailbox", _real_mailbox)

except ModuleNotFoundError:
    # Real implementation absent – keep the stub in place.
    pass

__all__ = ["mailbox", "MessageHandler"] 