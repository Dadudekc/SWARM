"""
Shared message types and enums.

This module contains shared types used across the messaging system.
"""

from typing import Dict, Any

from .common import Message, MessageMode, MessagePriority


# Re-export for backward compatibility
__all__ = ["Message", "MessageMode", "MessagePriority"]
