import logging
from pathlib import Path
from typing import Optional, List
from enum import Enum

# Constants
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class LogLevel(Enum):
    """Logging levels as an enum for type safety."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LogConfig:
    """Configuration for logging setup."""
    def __init__(
        self,
        log_dir: Optional[str] = DEFAULT_LOG_DIR,
        level: str = DEFAULT_LOG_LEVEL,
        format: str = DEFAULT_LOG_FORMAT,
        date_format: str = DEFAULT_DATE_FORMAT,
        batch_size: int = 100,
        batch_timeout: float = 60.0,
        rotation_size: int = 1024 * 1024,  # 1MB
        max_files: int = 5,
        rotation_check_interval: float = 300.0,
        cleanup_interval: float = 3600.0,
        use_temp_dir: bool = False,
        use_json: bool = True,
        use_text: bool = True,
        enable_discord: bool = False,
        discord_webhook_url: Optional[str] = None,
        discord_levels: Optional[List[str]] = None
    ):
        # Validate log level
        try:
            self.level = LogLevel[level.upper()]
        except KeyError:
            raise ValueError(f"Invalid log level: {level}. Must be one of: {[l.name for l in LogLevel]}")
        
        self.log_dir = log_dir
        self.format = format
        self.date_format = date_format
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.rotation_size = rotation_size
        self.max_files = max_files
        self.rotation_check_interval = rotation_check_interval
        self.cleanup_interval = cleanup_interval
        self.use_temp_dir = use_temp_dir
        self.use_json = use_json
        self.use_text = use_text
        self.enable_discord = enable_discord
        self.discord_webhook_url = discord_webhook_url
        self.discord_levels = discord_levels or []

def setup_logging(
    log_dir: Optional[str] = None,
    level: str = DEFAULT_LOG_LEVEL,
    format: str = DEFAULT_LOG_FORMAT
) -> None:
    """Configure logging for the application.
    
    Args:
        log_dir: Directory to store log files. If None, logs to console only
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(format)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_dir is provided
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / "app.log")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler) 