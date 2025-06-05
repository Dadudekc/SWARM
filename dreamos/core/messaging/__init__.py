"""
Messaging module for Dream.OS.
"""

from .common import Message
from .enums import MessageMode, MessagePriority, MessageType, TaskStatus, TaskPriority
from .unified_message_system import MessageSystem
from .cell_phone import send_message
try:
    from .phones import Phone, CaptainPhone
except Exception:  # pragma: no cover - optional dependency
    Phone = CaptainPhone = None
try:
    from dreamos.core.message_processor import MessageProcessor
except Exception:  # pragma: no cover - optional dependency
    MessageProcessor = None

__all__ = [
    "Message",
    "MessageMode",
    "MessagePriority",
    "MessageType",
    "TaskStatus",
    "TaskPriority",
    "MessageSystem",
    "Phone",
    "CaptainPhone",
    "MessageProcessor",
    "send_message"
]
