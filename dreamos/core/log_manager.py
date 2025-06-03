"""
Log Manager Module
----------------
Re-exports functionality from social.utils.log_manager.
"""

from social.utils.log_manager import LogManager, LogEntry
from social.utils.log_config import LogConfig

__all__ = ['LogManager', 'LogEntry', 'LogConfig'] 