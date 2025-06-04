"""
Messaging module for Dream.OS.
"""

from .common import Message
from .enums import MessageMode, MessagePriority, MessageType, TaskStatus, TaskPriority
from .unified_message_system import MessageSystem
from .phones import Phone, CaptainPhone
from dreamos.core.message_processor import MessageProcessor

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
    "MessageProcessor"
]
