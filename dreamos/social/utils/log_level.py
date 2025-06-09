"""
Log Level Module
---------------
Defines logging levels for the system.
"""

import logging
from enum import Enum, auto
from typing import Union

__all__ = ['LogLevel', 'from_str', 'value']

class LogLevel(Enum):
    """Logging levels for the system.
    
    Attributes:
        DEBUG: Detailed information for debugging
        INFO: General information about program execution
        WARNING: Indicates a potential problem
        ERROR: A more serious problem
        CRITICAL: A critical problem that may prevent the program from running
    """
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    
    @classmethod
    def from_str(cls, level: str) -> "LogLevel":
        """Create level from string.
        
        Args:
            level: Level name
            
        Returns:
            LogLevel instance
            
        Raises:
            ValueError: If level is invalid
        """
        try:
            return cls[level.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}")
            
    def __str__(self) -> str:
        """Get string representation of log level.
        
        Returns:
            str: Name of log level
        """
        return self.name
        
    @property
    def value(self) -> int:
        """Get the numeric value of the log level.
        
        Returns:
            int: Numeric value matching logging module constants
        """
        return self._value_

# Export functions for convenience
from_str = LogLevel.from_str
value = LogLevel.value 
