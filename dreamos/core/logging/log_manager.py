"""Log Manager
-----------
Manages logging for the Dream.OS system.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

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
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize log manager.
        
        Args:
            config: Optional log configuration
        """
        self._config = config or LogConfig()
        self._setup_logging()
    
    @classmethod
    def configure(cls, config: Optional[LogConfig] = None):
        """Configure the log manager.
        
        Args:
            config: Optional log configuration
        """
        cls._config = config or LogConfig()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logger
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(self._config.level.value)
        
        # Create formatter
        formatter = logging.Formatter(self._config.format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if path specified
        if self._config.file_path:
            os.makedirs(os.path.dirname(self._config.file_path), exist_ok=True)
            file_handler = logging.FileHandler(self._config.file_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
    def debug(self, message: str, **kwargs):
        """Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger(self.__class__.__name__).debug(message, extra=kwargs)
        
    def info(self, message: str, **kwargs):
        """Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger(self.__class__.__name__).info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger(self.__class__.__name__).warning(message, extra=kwargs)
        
    def error(self, message: str, **kwargs):
        """Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger(self.__class__.__name__).error(message, extra=kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger(self.__class__.__name__).critical(message, extra=kwargs)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            'total_entries': len(self._loggers),
            'entries_by_level': {
                level.name: sum(1 for logger in self._loggers.values() 
                              if logger.level == level.value)
                for level in LogLevel
            }
        }
        
    def shutdown(self):
        """Shutdown the log manager."""
        for logger in self._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler) 