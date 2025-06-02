"""
Log Manager Module
-----------------
Manages logging operations and coordinates between different logging components.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import os
import json
import threading
import logging
import tempfile
from contextlib import contextmanager
import platform
import time
import atexit
import portalocker

from .log_config import LogConfig
from .log_writer import LogWriter, LogEntry
from .log_batcher import LogBatcher
from .log_rotator import LogRotator
from .log_metrics import LogMetrics

# Configure logging
logger = logging.getLogger("LogManager")
logging.basicConfig(level=logging.DEBUG)

class LogManager:
    """Manages logging operations and coordinates between different logging components."""
    
    _instance = None
    _init_lock = threading.RLock()  # CHANGED: Use RLock for reentrancy
    _operation_lock = threading.RLock()  # CHANGED: Use RLock for reentrancy
    _initialized = False
    _file_locks = {}  # Track active file locks
    _cleanup_registered = False
    
    def __new__(cls, config: Optional[LogConfig] = None):
        """Ensure singleton instance with thread safety.
        
        Args:
            config: Optional logging configuration
        """
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    if not cls._cleanup_registered:
                        atexit.register(cls._cleanup_all_locks)
                        cls._cleanup_registered = True
        return cls._instance
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize the log manager with thread safety.
        
        Args:
            config: Optional logging configuration
        """
        if not self._initialized:
            with self._init_lock:
                if not self._initialized:
                    try:
                        self._initialize(config)
                        self._initialized = True
                    except Exception as e:
                        logger.error(f"Failed to initialize LogManager: {str(e)}")
                        self._initialized = False  # Reset initialization flag on failure
                        raise
    
    def _initialize(self, config: Optional[LogConfig] = None) -> None:
        """Initialize the log manager with configuration.
        
        Args:
            config: Optional configuration
        """
        # Use provided config or create default
        self.config = config or LogConfig(str(Path.cwd() / "logs"))
        
        # Create components
        self.batcher = LogBatcher(
            batch_size=self.config.batch_size,
            batch_timeout=self.config.batch_timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            test_mode=self.config.test_mode
        )
        self.writer = LogWriter(self.config.log_dir)
        self.rotator = LogRotator(self.config.log_dir)
        self.metrics = LogMetrics()
        
        # Setup log directory
        self._setup_log_directory()
        
        # Register cleanup handler
        if not self._cleanup_registered:
            atexit.register(self._cleanup_all_locks)
            self._cleanup_registered = True
    
    def _setup_log_directory(self) -> None:
        """Set up the log directory with proper permissions."""
        try:
            # Create log directory if it doesn't exist
            self.config.log_dir = Path(self.config.log_dir)
            self.config.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = self.config.log_dir / ".test_write"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                raise PermissionError(f"Log directory {self.config.log_dir} is not writable: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to set up log directory: {str(e)}")
            raise
    
    def _acquire_lock(self, f, log_file: str, timeout: int = 5) -> None:
        """Acquire a file lock with timeout.
        
        Args:
            f: File object to lock
            log_file: Path to the log file
            timeout: Maximum time to wait for lock in seconds
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        logger.debug(f"🔒 Attempting lock on: {log_file}")
        start = time.time()
        while True:
            try:
                portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
                logger.debug(f"✅ Lock acquired: {log_file}")
                return
            except portalocker.exceptions.LockException:
                if time.time() - start > timeout:
                    logger.error(f"⛔ Timeout locking file: {log_file}")
                    raise TimeoutError(f"Timeout acquiring lock on {log_file}")
                time.sleep(0.1)
    
    def _release_lock(self, f, log_file: str) -> None:
        """Release a file lock.
        
        Args:
            f: File object to unlock
            log_file: Path to the log file
        """
        logger.debug(f"🔓 Releasing lock: {log_file}")
        try:
            portalocker.unlock(f)
            logger.debug(f"✅ Lock released: {log_file}")
        except Exception as e:
            logger.error(f"Failed to release lock for {log_file}: {str(e)}")
    
    @classmethod
    def _cleanup_all_locks(cls):
        """Clean up all file locks."""
        for file_path, lock_info in list(cls._file_locks.items()):
            try:
                if lock_info['file'].fileno() != -1:  # Check if file is still open
                    logger.debug(f"Cleaning up lock for {file_path}")
                    portalocker.unlock(lock_info['file'])
                lock_info['file'].close()
                if lock_info['lock_file'].exists():
                    lock_info['lock_file'].unlink()
            except Exception as e:
                logger.error(f"Failed to cleanup lock for {file_path}: {str(e)}")
            finally:
                cls._file_locks.pop(file_path, None)
    
    @contextmanager
    def _get_file_lock(self, file_path: Path):
        """Get a file lock for thread-safe operations.
        
        Args:
            file_path: Path to lock
        """
        lock_file = file_path.with_suffix(file_path.suffix + '.lock')
        lock_info = None
        
        try:
            # Create lock file
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            lock_fd = open(lock_file, 'w')
            
            # Try to acquire lock with timeout
            self._acquire_lock(lock_fd, str(file_path))
            
            # Store lock info
            lock_info = {
                'file': lock_fd,
                'lock_file': lock_file
            }
            self._file_locks[str(file_path)] = lock_info
            
            yield
            
        finally:
            if lock_info:
                try:
                    if lock_info['file'].fileno() != -1:  # Check if file is still open
                        self._release_lock(lock_info['file'], str(file_path))
                    lock_info['file'].close()
                    if lock_info['lock_file'].exists():
                        lock_info['lock_file'].unlink()
                except Exception as e:
                    logger.error(f"Failed to release lock for {file_path}: {str(e)}")
                finally:
                    self._file_locks.pop(str(file_path), None)
    
    def write_log(
        self,
        platform: str,
        status: str,
        message: str,
        level: str = "INFO",
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        format: str = "json"
    ) -> bool:
        """Write a log entry with thread safety.
        
        Args:
            platform: Platform name
            status: Operation status
            message: Log message
            level: Log level
            tags: Optional tags
            metadata: Optional metadata
            error: Optional error message
            format: Output format
            
        Returns:
            bool: True if write was successful
        """
        try:
            # Create log entry
            entry = LogEntry(
                platform=platform,
                status=status,
                message=message,
                level=level,
                timestamp=datetime.now(),
                tags=tags,
                metadata=metadata,
                error=error
            )
            
            # Add to batch with thread safety
            with self._operation_lock:
                if self.batcher.add(entry.__dict__):
                    # Update metrics
                    self.metrics.increment_logs(
                        platform=platform,
                        level=level,
                        status=status,
                        format_type=format
                    )
                    return True
                
                # Batch is full, flush it
                self._write_batch()
                
                # Try adding again
                if self.batcher.add(entry.__dict__):
                    self.metrics.increment_logs(
                        platform=platform,
                        level=level,
                        status=status,
                        format_type=format
                    )
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to write log: {str(e)}")
            self.metrics.record_error(str(e))
            return False
    
    def _write_batch(self) -> None:
        """Write the current batch of entries with thread safety."""
        with self._operation_lock:
            entries = self.batcher.get_entries()
            for entry in entries:
                self.writer.write_log(entry)
    
    def _flush_all_batches(self) -> None:
        """Flush all pending batches with thread safety."""
        with self._operation_lock:
            self._write_batch()
            self.batcher.clear()
    
    def flush(self) -> None:
        """Flush any pending log entries with thread safety."""
        with self._operation_lock:
            self._write_batch()
    
    def read_logs(
        self,
        platform: str,
        level: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        format: str = "json"
    ) -> List[Dict[str, Any]]:
        """Read logs for a platform with filtering.
        
        Args:
            platform: Platform to read logs for
            level: Optional level filter
            status: Optional status filter
            tags: Optional tags filter
            format: Log file format
            
        Returns:
            List of log entries
        """
        with self._operation_lock:
            try:
                # Read all logs for platform
                entries = self.writer.read_logs(platform, format=format)
                
                # Apply filters
                if level:
                    entries = [e for e in entries if e["level"] == level]
                if status:
                    entries = [e for e in entries if e["status"] == status]
                if tags:
                    entries = [e for e in entries if all(tag in e.get("tags", []) for tag in tags)]
                
                return entries
            except Exception as e:
                logger.error(f"Failed to read logs: {str(e)}")
                return []
    
    def cleanup(self) -> None:
        """Clean up old log files."""
        with self._operation_lock:
            try:
                self.rotator.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup logs: {str(e)}")
    
    def reset(self) -> None:
        """Reset the log manager state."""
        with self._operation_lock:
            self.batcher.clear()
            self.metrics.reset()
    
    @classmethod
    def reset_singleton(cls) -> None:
        """Reset the singleton instance."""
        with cls._init_lock:
            if cls._instance is not None:
                try:
                    cls._instance.shutdown()
                except Exception as e:
                    logger.error(f"Error during singleton reset: {str(e)}")
                finally:
                    cls._instance = None
                    cls._initialized = False
    
    def shutdown(self) -> None:
        """Shutdown the log manager."""
        with self._operation_lock:
            try:
                self._flush_all_batches()
                self._cleanup_all_locks()
            except Exception as e:
                logger.error(f"Failed to shutdown log manager: {str(e)}")
            finally:
                self._initialized = False
    
    def info(self, platform: str, status: str, message: str, **kwargs) -> bool:
        """Write an info level log entry."""
        return self.write_log(platform, status, message, level="INFO", **kwargs)
    
    def warning(self, platform: str, status: str, message: str, **kwargs) -> bool:
        """Write a warning level log entry."""
        return self.write_log(platform, status, message, level="WARNING", **kwargs)
    
    def error(self, platform: str, status: str, message: str, **kwargs) -> bool:
        """Write an error level log entry."""
        return self.write_log(platform, status, message, level="ERROR", **kwargs)
    
    def debug(self, platform: str, status: str, message: str, **kwargs) -> bool:
        """Write a debug level log entry."""
        return self.write_log(platform, status, message, level="DEBUG", **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        with self._operation_lock:
            return self.metrics.get_metrics()

    @property
    def log_dir(self) -> Path:
        """Get the log directory path.
        
        Returns:
            Path object pointing to the log directory
        """
        return self.config.log_dir 