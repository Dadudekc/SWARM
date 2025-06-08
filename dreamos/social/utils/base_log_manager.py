"""
Log Level Definitions
-------------------
Provides standard log level definitions for consistent logging across the application.
"""

from enum import Enum

class LogLevel(Enum):
    """Standard log levels for consistent logging across the application."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL" 
