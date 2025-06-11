"""
Message Module

Defines core message types and structures for the Dream.OS messaging system.
"""

import logging
from typing import Dict, Any

from .common import Message, MessageContext
from .enums import MessageMode, MessagePriority, MessageType

logger = logging.getLogger('messaging.message')


# Re-export for backward compatibility
__all__ = ["Message", "MessageContext", "MessageMode", "MessagePriority", "MessageType"]
