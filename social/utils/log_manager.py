"""
Dream.OS Logging System
======================

A robust, extensible logging system for the Dream.OS swarm platform.
Implements structured logging with rotation, compression, and real-time monitoring capabilities.

Architecture:
- LogManager: Core singleton managing log operations
- LogRotator: Handles log rotation and compression
- LogReader: Manages log reading and filtering
- LogMonitor: Real-time log monitoring and alerts
- LogMetrics: Tracks logging metrics and performance

Quality Standards:
- Type hints and docstrings for all functions
- Comprehensive error handling
- Performance optimization
- Thread safety
- Real-time monitoring
- Metrics collection
"""

import os
import json
import gzip
import shutil
import logging
import threading
import queue
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

# Constants
DEFAULT_LOG_DIR = os.path.join(os.getcwd(), "social", "logs")
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_AGE = 30  # days
COMPRESS_AFTER = 7  # days
MAX_WORKERS = 4
METRICS_INTERVAL = 60  # seconds

_file_locks = {}
_file_locks_global = threading.Lock()

def get_file_lock(file_path: Path):
    with _file_locks_global:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]

class LogLevel(Enum):
    """Standardized log levels with numeric values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

@dataclass
class LogMetrics:
    """Tracks logging system metrics."""
    total_logs: int = 0
    total_bytes: int = 0
    rotation_count: int = 0
    compression_count: int = 0
    error_count: int = 0
    last_rotation: Optional[datetime] = None
    last_compression: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class LogConfig:
    """Configuration for the logging system."""
    log_dir: str = DEFAULT_LOG_DIR
    max_size: int = MAX_LOG_SIZE
    max_age: int = MAX_LOG_AGE
    compress_after: int = COMPRESS_AFTER
    max_workers: int = MAX_WORKERS
    metrics_interval: int = METRICS_INTERVAL
    enable_monitoring: bool = True
    enable_metrics: bool = True

class LogRotator:
    """Handles log rotation and compression."""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self._lock = threading.Lock()
    
    def should_rotate(self, file_path: Path) -> bool:
        """Check if a log file should be rotated."""
        try:
            return file_path.stat().st_size > self.config.max_size
        except OSError:
            return False
    
    def should_compress(self, file_path: Path) -> bool:
        """Check if a log file should be compressed."""
        try:
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_age.days > self.config.compress_after and not str(file_path).endswith('.gz')
        except OSError:
            return False
    
    def rotate(self, file_path: Path) -> Optional[Path]:
        """Rotate a log file."""
        with get_file_lock(file_path):
            try:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                rotated_path = file_path.with_suffix(f".{timestamp}.json")
                shutil.move(file_path, rotated_path)
                # After rotation, create a new empty file
                with open(file_path, 'w') as f:
                    json.dump([], f)
                return rotated_path
            except OSError as e:
                logging.error(f"Failed to rotate log file {file_path}: {e}")
                return None
    
    def compress(self, file_path: Path) -> bool:
        """Compress a log file."""
        with get_file_lock(file_path):
            try:
                with open(file_path, 'rb') as f_in:
                    with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file_path)
                return True
            except OSError as e:
                logging.error(f"Failed to compress log file {file_path}: {e}")
                return False
    
    def cleanup_old_logs(self) -> None:
        """Remove logs older than max_age."""
        try:
            current_time = datetime.now()
            for log_file in Path(self.config.log_dir).glob("*.json*"):
                try:
                    file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
                    if self.should_compress(log_file):
                        self.compress(log_file)
                    elif file_age.days > self.config.max_age:
                        os.remove(log_file)
                except OSError:
                    continue
        except Exception as e:
            logging.error(f"Failed to cleanup old logs: {e}")

class LogReader:
    """Manages log reading and filtering."""
    
    def __init__(self, config: LogConfig):
        self.config = config
    
    def read_logs(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        level: Optional[LogLevel] = None
    ) -> List[Dict[str, Any]]:
        """Read and filter logs."""
        try:
            log_files = sorted(Path(self.config.log_dir).glob(f"{platform}-*.json*"))
            if not log_files:
                return []
            
            all_logs = []
            for log_file in log_files:
                try:
                    logs = self._read_log_file(log_file)
                    all_logs.extend(logs)
                except Exception as e:
                    logging.error(f"Error reading log file {log_file}: {e}")
                    continue
            
            return self._filter_logs(all_logs, start_date, end_date, status, tags, level)
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            return []
    
    def _read_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read a single log file."""
        try:
            if str(file_path).endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r') as f:
                    data = json.load(f)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            logging.error(f"Error reading log file {file_path}: {e}")
            return []
    
    def _filter_logs(
        self,
        logs: List[Dict[str, Any]],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        status: Optional[str],
        tags: Optional[List[str]],
        level: Optional[LogLevel]
    ) -> List[Dict[str, Any]]:
        """Filter logs based on criteria."""
        filtered_logs = []
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp'])
                
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue
                if status and log['status'] != status:
                    continue
                if tags and not all(tag in log['tags'] for tag in tags):
                    continue
                if level and LogLevel[log['level']].value < level.value:
                    continue
                
                filtered_logs.append(log)
            except (KeyError, ValueError):
                continue
        
        return filtered_logs

class LogMonitor:
    """Real-time log monitoring and alerts."""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
        self._queue = queue.Queue()
        self._running = False
        self._thread = None
    
    def start(self) -> None:
        """Start the monitoring thread."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
    
    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join()
    
    def add_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a log observer."""
        self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a log observer."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                log_entry = self._queue.get(timeout=1)
                for observer in self._observers:
                    try:
                        observer(log_entry)
                    except Exception as e:
                        logging.error(f"Error in log observer: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in monitor loop: {e}")
    
    def notify(self, log_entry: Dict[str, Any]) -> None:
        """Notify observers of a new log entry."""
        self._queue.put(log_entry)

class PerformanceMetrics:
    """Tracks performance metrics for logging operations."""
    def __init__(self):
        self._write_times: List[float] = []
        self._read_times: List[float] = []
        self._rotation_times: List[float] = []
        self._compression_times: List[float] = []
        self._lock = threading.Lock()
    
    def record_write(self, duration: float) -> None:
        with self._lock:
            self._write_times.append(duration)
            if len(self._write_times) > 1000:  # Keep last 1000 measurements
                self._write_times.pop(0)
    
    def record_read(self, duration: float) -> None:
        with self._lock:
            self._read_times.append(duration)
            if len(self._read_times) > 1000:
                self._read_times.pop(0)
    
    def record_rotation(self, duration: float) -> None:
        with self._lock:
            self._rotation_times.append(duration)
            if len(self._rotation_times) > 100:
                self._rotation_times.pop(0)
    
    def record_compression(self, duration: float) -> None:
        with self._lock:
            self._compression_times.append(duration)
            if len(self._compression_times) > 100:
                self._compression_times.pop(0)
    
    def get_metrics(self) -> Dict[str, float]:
        with self._lock:
            return {
                "avg_write_time": sum(self._write_times) / len(self._write_times) if self._write_times else 0,
                "avg_read_time": sum(self._read_times) / len(self._read_times) if self._read_times else 0,
                "avg_rotation_time": sum(self._rotation_times) / len(self._rotation_times) if self._rotation_times else 0,
                "avg_compression_time": sum(self._compression_times) / len(self._compression_times) if self._compression_times else 0,
                "write_count": len(self._write_times),
                "read_count": len(self._read_times),
                "rotation_count": len(self._rotation_times),
                "compression_count": len(self._compression_times)
            }

class LogManager:
    """Core logging system manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance (for test isolation)."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.shutdown()
                except Exception:
                    pass
                cls._instance = None

    def __new__(cls, config: Optional[LogConfig] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize(config or LogConfig())
            return cls._instance
    
    def _initialize(self, config: LogConfig) -> None:
        """Initialize the logging system."""
        self.config = config
        self.rotator = LogRotator(config)
        self.reader = LogReader(config)
        self.monitor = LogMonitor(config) if config.enable_monitoring else None
        self.metrics = LogMetrics() if config.enable_metrics else None
        self._executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self._perf_metrics = PerformanceMetrics()
        
        # Create log directory
        try:
            if not os.path.exists(config.log_dir):
                os.makedirs(config.log_dir, exist_ok=True)
            # Check write permission
            testfile = Path(config.log_dir) / "__testwrite__"
            with open(testfile, 'w') as f:
                f.write('test')
            os.remove(testfile)
        except Exception as e:
            raise RuntimeError(f"Failed to create or write to log directory: {e}")
        
        # Start monitoring if enabled
        if self.monitor:
            self.monitor.start()
        
        # Start metrics collection if enabled
        if self.metrics:
            self._start_metrics_collection()
    
    def _start_metrics_collection(self) -> None:
        """Start periodic metrics collection."""
        def collect_metrics():
            while True:
                try:
                    self._update_metrics()
                    time.sleep(self.config.metrics_interval)
                except Exception as e:
                    logging.error(f"Error collecting metrics: {e}")
        
        threading.Thread(target=collect_metrics, daemon=True).start()
    
    def _update_metrics(self) -> None:
        """Update logging metrics."""
        try:
            total_size = sum(
                f.stat().st_size
                for f in Path(self.config.log_dir).glob("*.json*")
            )
            self.metrics.total_bytes = total_size
            self.metrics.performance_metrics = self._perf_metrics.get_metrics()
        except Exception as e:
            logging.error(f"Error updating metrics: {e}")
    
    def write_log(
        self,
        platform: str,
        status: str,
        tags: Optional[List[str]] = None,
        ai_output: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = LogLevel.INFO,
        sync: bool = False  # NEW: allow synchronous write for tests
    ) -> None:
        """Write a log entry."""
        def _write():
            start_time = time.time()
            try:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "platform": platform,
                    "status": status,
                    "level": level.name,
                    "tags": tags or [],
                    "ai_output": ai_output,
                    "error": error,
                    "metadata": metadata or {}
                }
                
                log_file = Path(self.config.log_dir) / f"{platform}-{datetime.now().strftime('%Y-%m-%d')}.json"
                with get_file_lock(log_file):
                    # Check rotation
                    if log_file.exists() and self.rotator.should_rotate(log_file):
                        rotation_start = time.time()
                        rotated_path = self.rotator.rotate(log_file)
                        self._perf_metrics.record_rotation(time.time() - rotation_start)
                        
                        if rotated_path and self.rotator.should_compress(rotated_path):
                            compression_start = time.time()
                            self.rotator.compress(rotated_path)
                            self._perf_metrics.record_compression(time.time() - compression_start)
                            if self.metrics:
                                self.metrics.compression_count += 1
                                self.metrics.last_compression = datetime.now()
                        if self.metrics:
                            self.metrics.rotation_count += 1
                            self.metrics.last_rotation = datetime.now()
                    
                    # Write log
                    try:
                        with open(log_file, 'r') as f:
                            data = json.load(f)
                            logs = data if isinstance(data, list) else [data]
                    except (FileNotFoundError, json.JSONDecodeError):
                        logs = []
                    
                    logs.append(log_entry)
                    
                    with open(log_file, 'w') as f:
                        json.dump(logs, f, indent=2)
                
                # Update metrics
                if self.metrics:
                    self.metrics.total_logs += 1
                
                # Notify observers
                if self.monitor:
                    self.monitor.notify(log_entry)
                
                self._perf_metrics.record_write(time.time() - start_time)
                
            except Exception as e:
                if self.metrics:
                    self.metrics.error_count += 1
                logging.error(f"Failed to write log: {e}")
                raise
        
        if sync:
            _write()
        else:
            try:
                self._executor.submit(_write)
            except RuntimeError as e:
                if "cannot schedule new futures after shutdown" in str(e):
                    self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
                    self._executor.submit(_write)
                else:
                    raise
    
    def read_logs(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        level: Optional[LogLevel] = None
    ) -> List[Dict[str, Any]]:
        """Read logs with filtering."""
        start_time = time.time()
        try:
            result = self.reader.read_logs(
                platform, start_date, end_date, status, tags, level
            )
            self._perf_metrics.record_read(time.time() - start_time)
            return result
        except Exception as e:
            self._perf_metrics.record_read(time.time() - start_time)
            raise
    
    def cleanup(self) -> None:
        """Clean up old logs."""
        self.rotator.cleanup_old_logs()
    
    def get_metrics(self) -> Optional[LogMetrics]:
        """Get current logging metrics."""
        return self.metrics
    
    def shutdown(self) -> None:
        """Shutdown the logging system."""
        if self.monitor:
            self.monitor.stop()
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)

# Initialize default instance
log_manager = LogManager() 