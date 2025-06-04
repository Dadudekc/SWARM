"""
Message Module

Defines core message types and structures for the Dream.OS messaging system.
"""

import logging
from typing import Dict, Any

from .common import Message, MessageMode, MessagePriority

logger = logging.getLogger('messaging.message')


# Re-export for backward compatibility
__all__ = ["Message", "MessageMode", "MessagePriority"]
