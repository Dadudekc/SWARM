"""
Unified logging system for Dream.OS.

This module provides a centralized logging system that handles all logging
across the project, including agent logs, bridge logs, and system logs.
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum

class LogLevel(Enum):
    """Log levels supported by the system."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LogCategory(Enum):
    """Categories of logs in the system."""
    AGENT = "agent"
    BRIDGE = "bridge"
    SYSTEM = "system"
    SOCIAL = "social"
    VALIDATION = "validation"
    METRICS = "metrics"

@dataclass
class LogConfig:
    """Configuration for a log category."""
    category: LogCategory
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    json_format: bool = False

class UnifiedLogger:
    """Unified logging system for Dream.OS."""
    
    def __init__(self, log_root: str = None):
        """Initialize the logging system.
        
        Args:
            log_root: Root directory for log files. If None, uses default.
        """
        self.log_root = log_root or os.path.join(os.path.dirname(__file__), "..", "..", "logs")
        self.loggers: Dict[LogCategory, logging.Logger] = {}
        self.configs: Dict[LogCategory, LogConfig] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for all categories."""
        # Create log directory if it doesn't exist
        os.makedirs(self.log_root, exist_ok=True)
        
        # Configure each category
        for category in LogCategory:
            config = self._get_default_config(category)
            self.configs[category] = config
            self._setup_category_logger(category, config)
    
    def _get_default_config(self, category: LogCategory) -> LogConfig:
        """Get default configuration for a log category.
        
        Args:
            category: Log category.
            
        Returns:
            LogConfig: Default configuration for the category.
        """
        return LogConfig(
            category=category,
            level=LogLevel.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            json_format=category in [LogCategory.METRICS, LogCategory.VALIDATION]
        )
    
    def _setup_category_logger(self, category: LogCategory, config: LogConfig):
        """Set up a logger for a specific category.
        
        Args:
            category: Log category.
            config: Log configuration.
        """
        logger = logging.getLogger(f"dreamos.{category.value}")
        logger.setLevel(config.level.value)
        
        # Create handlers
        handlers = []
        
        # File handler
        log_file = os.path.join(self.log_root, f"{category.value}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.max_size,
            backupCount=config.backup_count
        )
        handlers.append(file_handler)
        
        # JSON file handler for metrics and validation
        if config.json_format:
            json_file = os.path.join(self.log_root, f"{category.value}.json")
            json_handler = logging.handlers.RotatingFileHandler(
                json_file,
                maxBytes=config.max_size,
                backupCount=config.backup_count
            )
            handlers.append(json_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        handlers.append(console_handler)
        
        # Set formatters
        if config.json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(config.format)
        
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        self.loggers[category] = logger
    
    def get_logger(self, category: LogCategory) -> logging.Logger:
        """Get a logger for a specific category.
        
        Args:
            category: Log category.
            
        Returns:
            logging.Logger: Logger for the category.
        """
        return self.loggers[category]
    
    def set_level(self, category: LogCategory, level: LogLevel):
        """Set the log level for a category.
        
        Args:
            category: Log category.
            level: Log level.
        """
        if category in self.loggers:
            self.loggers[category].setLevel(level.value)
            self.configs[category].level = level
    
    def log(self, category: LogCategory, level: LogLevel, message: str, **kwargs):
        """Log a message.
        
        Args:
            category: Log category.
            level: Log level.
            message: Log message.
            **kwargs: Additional fields for JSON logging.
        """
        logger = self.get_logger(category)
        
        if self.configs[category].json_format:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": level.name,
                "message": message,
                **kwargs
            }
            logger.log(level.value, json.dumps(log_data))
        else:
            logger.log(level.value, message)

class JsonFormatter(logging.Formatter):
    """Formatter that outputs JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            str: JSON-formatted log record.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

# Global logger instance
logger = UnifiedLogger()

def get_logger(category: LogCategory) -> logging.Logger:
    """Get a logger for a specific category.
    
    Args:
        category: Log category.
        
    Returns:
        logging.Logger: Logger for the category.
    """
    return logger.get_logger(category)

def log(category: LogCategory, level: LogLevel, message: str, **kwargs):
    """Log a message using the global logger.
    
    Args:
        category: Log category.
        level: Log level.
        message: Log message.
        **kwargs: Additional fields for JSON logging.
    """
    logger.log(category, level, message, **kwargs) 