"""
Logging Utilities
--------------
Core logging configuration and helpers for Dream.OS.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def configure_logging(
    level: str = "INFO",
    format: str = "%(asctime)s | %(levelname)s | %(message)s",
    log_file: Optional[Path] = None,
    log_dir: Optional[Path] = None
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level
        format: Log message format
        log_file: Optional log file path
        log_dir: Optional log directory
    """
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / log_file
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_platform_event(
    logger: logging.Logger,
    platform: str,
    status: str,
    message: str,
    tags: Optional[list] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """Log a platform event.
    
    Args:
        logger: Logger instance
        platform: Platform name
        status: Event status
        message: Event message
        tags: Optional tags
        extra: Optional extra data
    """
    log_data = {
        "platform": platform,
        "status": status,
        "message": message,
        "tags": tags or []
    }
    if extra:
        log_data.update(extra)
    
    logger.info(log_data) 