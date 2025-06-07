"""Log Manager
-----------
Manages logging for social media operations.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    """Manages logging for social media operations."""
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize the log manager.
        
        Args:
            config: Optional log configuration
        """
        self.config = config or LogConfig()
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logger
        logger = logging.getLogger('social')
        logger.setLevel(self.config.level.value)
        
        # Create formatter
        formatter = logging.Formatter(self.config.format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if path specified
        if self.config.file_path:
            os.makedirs(os.path.dirname(self.config.file_path), exist_ok=True)
            file_handler = logging.FileHandler(self.config.file_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
    def debug(self, message: str, **kwargs):
        """Log a debug message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger('social').debug(message, extra=kwargs)
        
    def info(self, message: str, **kwargs):
        """Log an info message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger('social').info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log a warning message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger('social').warning(message, extra=kwargs)
        
    def error(self, message: str, **kwargs):
        """Log an error message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger('social').error(message, extra=kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log a critical message.
        
        Args:
            message: The message to log
            **kwargs: Additional context
        """
        logging.getLogger('social').critical(message, extra=kwargs) 