"""
Log Manager Stub
--------------
Minimal stub implementation to unblock tests.
"""

import logging
from typing import Any, Optional

class LogManager:
    """Stub implementation of LogManager."""
    
    def __init__(self, name: str = "stub_logger"):
        """Initialize stub logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
    
    def log(self, message: str, level: str = "info", **kwargs: Any) -> None:
        """Log a message."""
        getattr(self.logger, level.lower())(message)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message) 