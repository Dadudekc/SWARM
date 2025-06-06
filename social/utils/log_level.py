"""Log level definitions."""

from enum import Enum, auto

class LogLevel(Enum):
    """Log levels for the system."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto() 