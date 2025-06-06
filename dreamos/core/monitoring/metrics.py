"""
Metrics collection and monitoring.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class LogMetrics:
    """Collects and manages logging metrics."""
    
    def __init__(self, config):
        """Initialize metrics collection.
        
        Args:
            config: Configuration object or dictionary containing log_dir
        """
        # Handle both dictionary and LogConfig objects
        if hasattr(config, 'log_dir'):
            self.log_dir = Path(config.log_dir)
        else:
            self.log_dir = Path(config.get('log_dir', 'logs'))
            
        self.metrics = {
            'message_count': 0,
            'error_count': 0,
            'last_error': None,
            'last_message': None
        }
        self.logger = logging.getLogger(__name__)
    
    def record_message(self, message: str):
        """Record a message in metrics.
        
        Args:
            message: The message content
        """
        self.metrics['message_count'] += 1
        self.metrics['last_message'] = {
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        self._save()
    
    def record_error(self, error: str):
        """Record an error in metrics.
        
        Args:
            error: The error message
        """
        self.metrics['error_count'] += 1
        self.metrics['last_error'] = {
            'content': error,
            'timestamp': datetime.now().isoformat()
        }
        self._save()
    
    def get_metrics(self) -> Dict:
        """Get current metrics.
        
        Returns:
            Dict: Current metrics data
        """
        return self.metrics
    
    def reset(self):
        """Reset metrics to initial state."""
        self.metrics = {
            'message_count': 0,
            'error_count': 0,
            'last_error': None,
            'last_message': None
        }
        self._save()
    
    def _save(self):
        """Save metrics to disk."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            metrics_file = self.log_dir / 'metrics.json'
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")

    def collect(self) -> Dict[str, Any]:
        """
        Walks through the log directory and gathers:
          - Total number of log files
          - Total size in bytes
          - Oldest and newest timestamps
        """
        total_size = 0
        file_count = 0
        oldest = None
        newest = None

        if not self.log_dir.exists():
            return {}

        for file_path in self.log_dir.rglob("*.log"):
            try:
                stat = file_path.stat()
                total_size += stat.st_size
                file_count += 1

                mtime = stat.st_mtime
                if oldest is None or mtime < oldest:
                    oldest = mtime
                if newest is None or mtime > newest:
                    newest = mtime
            except (OSError, PermissionError):
                continue

        self.metrics = {
            "total_size_bytes": total_size,
            "file_count": file_count,
            "oldest_timestamp": time.ctime(oldest) if oldest else None,
            "newest_timestamp": time.ctime(newest) if newest else None,
        }
        return self.metrics 