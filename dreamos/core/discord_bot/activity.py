"""
Discord Activity Types
--------------------
Defines activity types for Discord bot status.
"""

from enum import IntEnum

class ActivityType(IntEnum):
    """Discord activity types."""
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

__all__ = ['ActivityType'] 