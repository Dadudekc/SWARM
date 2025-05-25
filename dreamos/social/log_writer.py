"""
Log Writer Module

Handles logging functionality for the social media components.
"""

import logging
import os
from typing import Optional
from datetime import datetime

def setup_logging(log_dir: Optional[str] = None) -> None:
    """Set up logging configuration.
    
    Args:
        log_dir: Optional directory for log files
    """
    # Configure logging
    logger = logging.getLogger('social')
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Create file handler
    log_file = os.path.join(log_dir, f'social_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Configure logging
logger = logging.getLogger('social')
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create file handler
log_file = os.path.join(log_dir, f'social_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def set_log_level(level: int) -> None:
    """Set the logging level.
    
    Args:
        level: Logging level (e.g. logging.INFO, logging.DEBUG)
    """
    logger.setLevel(level)
    file_handler.setLevel(level)
    console_handler.setLevel(level)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Optional name for the logger
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'social.{name}')
    return logger 

# --- Test stubs for log_writer API ---
LOGS_DIR = os.path.join(os.getcwd(), 'logs')
MAX_LOG_SIZE = 1024 * 1024 * 5  # 5MB
MAX_LOG_AGE = 7  # days
COMPRESS_AFTER = 3  # days

def rotate_logs(*args, **kwargs):
    pass

def write_json_log(*args, **kwargs):
    pass

def read_logs(*args, **kwargs):
    return [] 