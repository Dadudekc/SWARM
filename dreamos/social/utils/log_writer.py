"""
Log Writer Module
----------------
Handles writing logs to files with proper locking and metrics tracking.
"""

import os
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from .file_locks import get_file_lock, ensure_log_dir
from .log_metrics import LogMetrics
from .log_cleanup import cleanup_old_logs, rotate_log, compress_old_logs

logger = logging.getLogger(__name__)

class LogWriter:
    """Handles writing logs to files with proper locking and metrics tracking."""
    
    def __init__(
        self,
        log_dir: str,
        platform: str,
        max_size_mb: int = 10,
        backup_count: int = 5,
        max_age_days: int = 30,
        compress_after_days: int = 7
    ):
        """Initialize the log writer.
        
        Args:
            log_dir: Directory to store logs
            platform: Platform name (e.g. 'twitter', 'discord')
            max_size_mb: Maximum log file size in MB
            backup_count: Number of backup files to keep
            max_age_days: Maximum age of logs in days
            compress_after_days: Age in days after which to compress
        """
        self.log_dir = log_dir
        self.platform = platform
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self.max_age_days = max_age_days
        self.compress_after_days = compress_after_days
        
        # Ensure log directory exists
        ensure_log_dir(log_dir)
        
        # Initialize metrics
        self.metrics = LogMetrics()
        self.metrics_file = os.path.join(log_dir, f"{platform}_metrics.json")
        self.metrics.load(self.metrics_file)
        
        # Clean up old logs
        cleanup_old_logs(log_dir, max_age_days)
        compress_old_logs(log_dir, compress_after_days)

    def write_log(
        self,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write a log entry.
        
        Args:
            level: Log level (e.g. 'info', 'error')
            message: Log message
            metadata: Additional metadata to include
        """
        try:
            # Prepare log entry
            entry = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'platform': self.platform,
                'message': message
            }
            if metadata:
                entry['metadata'] = metadata
                
            # Get log file path
            log_file = os.path.join(self.log_dir, f"{self.platform}.log")
            
            # Check if rotation needed
            rotate_log(log_file, self.max_size_mb, self.backup_count)
            
            # Write log entry with proper locking
            with get_file_lock(log_file) as f:
                f.write(json.dumps(entry) + '\n')
                
            # Update metrics
            self.metrics.update(level, self.platform)
            self.metrics.save(self.metrics_file)
            
        except Exception as e:
            logger.error(f"Error writing log: {e}")
            raise

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.get_metrics()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the metrics."""
        return self.metrics.get_summary()

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.metrics.save(self.metrics_file) 