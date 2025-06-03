"""
Log Level Module
---------------
Defines logging levels for the system.
"""

import logging
from enum import Enum
from typing import Union

class LogLevel(Enum):
    """Logging levels for the system.
    
    Attributes:
        DEBUG: Detailed information for debugging
        INFO: General information about program execution
        WARNING: Indicates a potential problem
        ERROR: A more serious problem
        CRITICAL: A critical problem that may prevent the program from running
    """
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    @classmethod
    def from_str(cls, level: Union[str, 'LogLevel']) -> 'LogLevel':
        """Convert string or LogLevel to LogLevel enum.
        
        Args:
            level: String representation of log level or LogLevel enum
            
        Returns:
            LogLevel: Corresponding enum value
            
        Raises:
            ValueError: If level string is invalid
        """
        # If already a LogLevel, return it
        if isinstance(level, cls):
            return level
            
        # If it's a string, try to convert it
        if isinstance(level, str):
            try:
                return cls[level.upper()]
            except KeyError:
                raise ValueError(f"Invalid log level: {level}. Must be one of: {[l.name for l in cls]}")
                
        # If it's an int, try to match it to a level
        if isinstance(level, int):
            for log_level in cls:
                if log_level.value == level:
                    return log_level
            raise ValueError(f"Invalid log level value: {level}")
            
        raise ValueError(f"Log level must be string, int, or LogLevel, got {type(level)}")
            
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