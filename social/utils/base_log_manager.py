"""
Base Log Manager Module

Provides base logging functionality and log level definitions.
"""

from enum import Enum

class BaseLogManager:
    """Base class for log managers with minimal functionality."""
    
    def __init__(self, config=None):
        """Initialize base log manager.
        
        Args:
            config: Optional configuration object
        """
        self.config = config
        self.logger = self  # Act as its own logger for fallback

    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def critical(self, msg): pass

class LogLevel(Enum):
    """Standard log levels for consistent logging across the application."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL" 