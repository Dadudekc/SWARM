"""
Dream.OS Messaging System

Provides a unified messaging system for agent communication.
"""

from .message import Message, MessageMode
from .processor import MessageProcessor
from .queue import MessageQueue
from .ui import MessageUI
from .cli import MessageCLI

__all__ = [
    'Message',
    'MessageMode',
    'MessageProcessor',
    'MessageQueue',
    'MessageUI',
    'MessageCLI'
] 