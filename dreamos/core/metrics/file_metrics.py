"""
File Metrics Module
----------------
Specialized metrics for file operations.
"""

from typing import Dict, Optional
from pathlib import Path
from .base import BaseMetrics

class FileMetrics(BaseMetrics):
    """Metrics for file operations."""
    
    def __init__(self, metrics_dir: Optional[str] = None):
        """Initialize file metrics.
        
        Args:
            metrics_dir: Optional directory to store metrics
        """
        super().__init__("file_metrics", metrics_dir)
        
    def record_read(self, path: str, bytes_read: int, encoding: str = "utf-8") -> None:
        """Record a file read operation.
        
        Args:
            path: File path
            bytes_read: Number of bytes read
            encoding: File encoding
        """
        self.increment("file_reads", tags={
            "path": str(Path(path).resolve()),
            "encoding": encoding
        })
        self.histogram("file_read_bytes", bytes_read)
        
    def record_write(self, path: str, bytes_written: int, encoding: str = "utf-8") -> None:
        """Record a file write operation.
        
        Args:
            path: File path
            bytes_written: Number of bytes written
            encoding: File encoding
        """
        self.increment("file_writes", tags={
            "path": str(Path(path).resolve()),
            "encoding": encoding
        })
        self.histogram("file_write_bytes", bytes_written)
        
    def record_error(self, path: str, operation: str, error: str) -> None:
        """Record a file operation error.
        
        Args:
            path: File path
            operation: Operation type (read/write)
            error: Error message
        """
        self.increment("file_errors", tags={
            "path": str(Path(path).resolve()),
            "operation": operation
        })
        
    def record_directory_operation(self, path: str, operation: str) -> None:
        """Record a directory operation.
        
        Args:
            path: Directory path
            operation: Operation type (create/delete/list)
        """
        self.increment("directory_operations", tags={
            "path": str(Path(path).resolve()),
            "operation": operation
        }) 