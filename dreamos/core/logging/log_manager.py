"""Log Manager
-----------
Manages logging for the Dream.OS system.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict

class LogLevel(Enum):
    """Log levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class LogConfig:
    """Log configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None

class LogManager:
    """Manages logging for the Dream.OS system."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _config: Optional[LogConfig] = None
    
    @classmethod
    def configure(cls, config: Optional[LogConfig] = None):
        """Configure the log manager.
        
        Args:
            config: Optional log configuration
        """
        cls._config = config or LogConfig()
        
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(cls._config.level.value if cls._config else LogLevel.INFO.value)
            
            # Create formatter
            formatter = logging.Formatter(
                cls._config.format if cls._config else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Add console handler if none exists
            if not logger.handlers:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
                
                # Add file handler if path specified
                if cls._config and cls._config.file_path:
                    os.makedirs(os.path.dirname(cls._config.file_path), exist_ok=True)
                    file_handler = logging.FileHandler(cls._config.file_path)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
            
            cls._loggers[name] = logger
            
        return cls._loggers[name]
        
    @classmethod
    def debug(cls, name: str, message: str, **kwargs):
        """Log a debug message.
        
        Args:
            name: Logger name
            message: The message to log
            **kwargs: Additional context
        """
        cls.get_logger(name).debug(message, extra=kwargs)
        
    @classmethod
    def info(cls, name: str, message: str, **kwargs):
        """Log an info message.
        
        Args:
            name: Logger name
            message: The message to log
            **kwargs: Additional context
        """
        cls.get_logger(name).info(message, extra=kwargs)
        
    @classmethod
    def warning(cls, name: str, message: str, **kwargs):
        """Log a warning message.
        
        Args:
            name: Logger name
            message: The message to log
            **kwargs: Additional context
        """
        cls.get_logger(name).warning(message, extra=kwargs)
        
    @classmethod
    def error(cls, name: str, message: str, **kwargs):
        """Log an error message.
        
        Args:
            name: Logger name
            message: The message to log
            **kwargs: Additional context
        """
        cls.get_logger(name).error(message, extra=kwargs)
        
    @classmethod
    def critical(cls, name: str, message: str, **kwargs):
        """Log a critical message.
        
        Args:
            name: Logger name
            message: The message to log
            **kwargs: Additional context
        """
        cls.get_logger(name).critical(message, extra=kwargs) 