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

__all__ = ["mailbox", "MessageHandler"] 