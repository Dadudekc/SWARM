"""
Simple Log Manager Module
------------------------
Provides a simple wrapper around Python's standard logging module.
"""

import logging
from typing import Optional, Dict, Any
from .log_config import setup_logging

class LogManager:
    """Simple wrapper around Python's logging module."""
    
    _instance = None  # Singleton instance for test compatibility
    
    def __init__(self, platform: str, log_dir: Optional[str] = None):
        """Initialize the log manager.
        
        Args:
            platform: Platform name (e.g., 'reddit', 'facebook')
            log_dir: Optional directory to store log files
        """
        self.platform = platform
        self.logger = logging.getLogger(f"social.{platform}")
        
        # Setup logging if not already configured
        if not logging.getLogger().handlers:
            setup_logging(log_dir)
        LogManager._instance = self
    
    @classmethod
    def reset_singleton(cls):
        cls._instance = None
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(message, extra=self._get_extra(**kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(message, extra=self._get_extra(**kwargs))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message."""
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=True, extra=self._get_extra(**kwargs))
        else:
            self.logger.error(message, extra=self._get_extra(**kwargs))
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(message, extra=self._get_extra(**kwargs))
    
    def _get_extra(self, **kwargs) -> Dict[str, Any]:
        """Get extra logging context."""
        return {
            "platform": self.platform,
            **kwargs
        } 