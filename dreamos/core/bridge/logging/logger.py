"""
Bridge Logger
-----------
Centralized logging for bridge operations.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeLogger:
    """Centralized logging for bridge operations."""
    
    def __init__(
        self,
        log_dir: Union[str, Path],
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the logger.
        
        Args:
            log_dir: Directory to store logs
            config: Optional configuration dictionary
        """
        self.log_dir = Path(log_dir)
        self.config = config or {}
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up loggers
        self._setup_loggers()
        
    def _setup_loggers(self) -> None:
        """Set up loggers for different components."""
        # Get log format
        log_format = self.config.get(
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Set up component loggers
        components = [
            "bridge",
            "outbox",
            "inbox",
            "processor",
            "validator",
            "metrics",
            "health"
        ]
        
        for component in components:
            # Create logger
            component_logger = logging.getLogger(f"bridge.{component}")
            component_logger.setLevel(logging.INFO)
            
            # Create file handler
            log_file = self.log_dir / f"{component}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            
            # Add handler
            component_logger.addHandler(file_handler)
            
    def log_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> None:
        """Log a message.
        
        Args:
            content: Message content
            metadata: Optional metadata
            level: Log level
        """
        # Get logger
        logger = logging.getLogger("bridge.outbox")
        
        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "content": content,
            "metadata": metadata or {}
        }
        
        # Log message
        log_method = getattr(logger, level.lower())
        log_method(json.dumps(entry))
        
    def log_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> None:
        """Log a response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            level: Log level
        """
        # Get logger
        logger = logging.getLogger("bridge.inbox")
        
        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "content": content,
            "metadata": metadata or {}
        }
        
        # Log response
        log_method = getattr(logger, level.lower())
        log_method(json.dumps(entry))
        
    def log_metric(
        self,
        name: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> None:
        """Log a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metadata: Optional metadata
            level: Log level
        """
        # Get logger
        logger = logging.getLogger("bridge.metrics")
        
        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "name": name,
            "value": value,
            "metadata": metadata or {}
        }
        
        # Log metric
        log_method = getattr(logger, level.lower())
        log_method(json.dumps(entry))
        
    def log_health(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> None:
        """Log health status.
        
        Args:
            status: Health status
            details: Optional details
            level: Log level
        """
        # Get logger
        logger = logging.getLogger("bridge.health")
        
        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "details": details or {}
        }
        
        # Log health
        log_method = getattr(logger, level.lower())
        log_method(json.dumps(entry))
        
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = "ERROR"
    ) -> None:
        """Log an error.
        
        Args:
            error: Error to log
            context: Optional context
            level: Log level
        """
        # Get logger
        logger = logging.getLogger("bridge")
        
        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(error),
            "type": error.__class__.__name__,
            "context": context or {}
        }
        
        # Log error
        log_method = getattr(logger, level.lower())
        log_method(json.dumps(entry))
        
    def get_logs(
        self,
        component: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get logs for a component.
        
        Args:
            component: Component name
            start_time: Optional start time
            end_time: Optional end time
            level: Optional log level
            
        Returns:
            List of log entries
        """
        # Get logger
        logger = logging.getLogger(f"bridge.{component}")
        
        # Get log file
        log_file = self.log_dir / f"{component}.log"
        
        if not log_file.exists():
            return []
            
        # Read logs
        logs = []
        with open(log_file) as f:
            for line in f:
                try:
                    # Parse log entry
                    entry = json.loads(line)
                    
                    # Filter by time
                    if start_time:
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time < start_time:
                            continue
                            
                    if end_time:
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time > end_time:
                            continue
                            
                    # Filter by level
                    if level and entry.get("level") != level:
                        continue
                        
                    logs.append(entry)
                    
                except json.JSONDecodeError:
                    continue
                    
        return logs 