"""
Tests for the Dream.OS Logging System.

This test suite verifies the functionality of the logging system components:
- LogManager: Core logging operations
- LogRotator: Log rotation and compression
- LogReader: Log reading and filtering
- LogMonitor: Real-time monitoring
- LogMetrics: Metrics collection
"""

import os
import json
import gzip
import pytest
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from social.utils.log_manager import (
    LogManager,
    LogConfig,
    LogLevel,
    LogMetrics,
    LogRotator,
    LogReader,
    LogMonitor
)

# Test constants
TEST_MAX_SIZE = 1024  # 1KB for testing
TEST_MAX_AGE = 1  # 1 day for testing
TEST_COMPRESS_AFTER = 1  # 1 day for testing
TEST_MAX_WORKERS = 2
TEST_METRICS_INTERVAL = 1
TEST_FILE_WAIT_TIMEOUT = 0.5
TEST_FILE_WAIT_INTERVAL = 0.05

class PerformanceMonitor:
    """Monitor test performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "write_time": [],
            "read_time": [],
            "rotation_time": [],
            "compression_time": [],
            "concurrent_write_time": []
        }
        self._lock = threading.Lock()
    
    def record_metric(self, metric_name: str, duration: float) -> None:
        """Record a performance metric."""
        with self._lock:
            if metric_name in self.metrics:
                self.metrics[metric_name].append(duration)
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics summary."""
        summary = {}
        with self._lock:
            for metric_name, durations in self.metrics.items():
                if durations:
                    summary[metric_name] = {
                        "min": min(durations),
                        "max": max(durations),
                        "avg": sum(durations) / len(durations),
                        "count": len(durations)
                    }
        return summary

@pytest.fixture(scope="session")
def perf_monitor():
    """Create a performance monitor instance."""
    return PerformanceMonitor()

@pytest.fixture(scope="session")
def test_config():
    """Create a test configuration with optimized settings."""
    return LogConfig(
        log_dir=os.path.join(os.getcwd(), "tests", "logs"),
        max_size=TEST_MAX_SIZE,
        max_age=TEST_MAX_AGE,
        compress_after=TEST_COMPRESS_AFTER,
        max_workers=TEST_MAX_WORKERS,
        metrics_interval=TEST_METRICS_INTERVAL,
        enable_monitoring=True,
        enable_metrics=True
    )

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset LogManager singleton before each test."""
    LogManager.reset_singleton()
    yield
    LogManager.reset_singleton()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for logs with cleanup."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    yield log_dir
    # Cleanup after test
    for file in log_dir.glob("*"):
        try:
            if file.is_file():
                file.unlink()
        except Exception:
            pass

@pytest.fixture
def log_manager(test_config, temp_log_dir):
    """Create a LogManager instance with test configuration."""
    test_config.log_dir = str(temp_log_dir)
    manager = LogManager(test_config)
    yield manager
    manager.shutdown()

def wait_for_file(file_path: Path, timeout: float = TEST_FILE_WAIT_TIMEOUT) -> bool:
    """Wait for a file to exist with optimized timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if file_path.exists():
            return True
        time.sleep(TEST_FILE_WAIT_INTERVAL)
    return False

def verify_log_content(log_file: Path, expected_count: int = 1) -> bool:
    """Verify log file content with error handling."""
    try:
        if not log_file.exists():
            return False
        with open(log_file) as f:
            logs = json.load(f)
            return len(logs) == expected_count
    except Exception:
        return False

def test_log_manager_singleton(test_config):
    """Test that LogManager is a singleton."""
    manager1 = LogManager(test_config)
    manager2 = LogManager(test_config)
    assert manager1 is manager2
    manager1.shutdown()

def test_write_log(log_manager, temp_log_dir, perf_monitor):
    """Test basic log writing with performance monitoring."""
    start_time = time.time()
    
    log_manager.write_log(
        platform="test_platform",
        status="test_status",
        tags=["test"],
        metadata={"test": "data"},
        sync=True
    )
    
    duration = time.time() - start_time
    perf_monitor.record_metric("write_time", duration)
    
    log_file = temp_log_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    assert wait_for_file(log_file)
    assert verify_log_content(log_file)
    
    with open(log_file) as f:
        logs = json.load(f)
        assert len(logs) == 1
        assert logs[0]["platform"] == "test_platform"
        assert logs[0]["status"] == "test_status"
        assert logs[0]["tags"] == ["test"]
        assert logs[0]["metadata"] == {"test": "data"}

def test_write_log_with_error(log_manager, temp_log_dir):
    """Test writing logs with error information."""
    log_manager.write_log(
        platform="test_platform",
        status="error_test",
        error="Test error message",
        level=LogLevel.ERROR,
        sync=True
    )
    
    log_file = temp_log_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    assert wait_for_file(log_file)
    assert verify_log_content(log_file)
    
    with open(log_file) as f:
        logs = json.load(f)
        assert logs[0]["error"] == "Test error message"
        assert logs[0]["level"] == "ERROR"

def test_log_rotation(log_manager, temp_log_dir):
    """Test log rotation functionality with verification."""
    log_file = temp_log_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    
    # Create a large log file efficiently
    large_log = ["x" * TEST_MAX_SIZE] * 2
    with open(log_file, 'w') as f:
        json.dump(large_log, f)
    
    # Write a new log entry to trigger rotation
    log_manager.write_log(
        platform="test_platform",
        status="rotation_test",
        sync=True
    )
    
    # Verify rotation
    assert log_file.exists()
    assert verify_log_content(log_file, expected_count=1)
    
    # Check rotated file
    rotated_files = list(temp_log_dir.glob("*.json.*"))
    assert len(rotated_files) == 1

def test_log_compression(log_manager, temp_log_dir):
    """Test log compression with verification."""
    # Create an old log file
    old_date = datetime.now() - timedelta(days=2)
    old_log_file = temp_log_dir / f"test_platform-{old_date.strftime('%Y-%m-%d')}.json"
    
    test_data = {"test": "data"}
    with open(old_log_file, 'w') as f:
        json.dump(test_data, f)
    
    # Set file modification time
    old_timestamp = old_date.timestamp()
    os.utime(old_log_file, (old_timestamp, old_timestamp))
    
    # Trigger cleanup
    log_manager.cleanup()
    
    # Verify compression
    compressed_file = old_log_file.with_suffix('.json.gz')
    assert compressed_file.exists()
    
    # Verify content
    with gzip.open(compressed_file, 'rt') as f:
        data = json.load(f)
        assert data == test_data

def test_read_logs(log_manager, temp_log_dir, perf_monitor):
    """Test reading logs with performance monitoring."""
    # Write test logs efficiently
    test_logs = [
        {
            "platform": "test_platform",
            "status": "success",
            "tags": ["test"],
            "sync": True
        },
        {
            "platform": "test_platform",
            "status": "failure",
            "tags": ["error"],
            "level": LogLevel.ERROR,
            "sync": True
        }
    ]
    
    for log_data in test_logs:
        log_manager.write_log(**log_data)
    
    # Test reading with performance monitoring
    start_time = time.time()
    all_logs = log_manager.read_logs("test_platform")
    duration = time.time() - start_time
    perf_monitor.record_metric("read_time", duration)
    
    assert len(all_logs) == 2
    
    # Test filtering with performance monitoring
    start_time = time.time()
    success_logs = log_manager.read_logs("test_platform", status="success")
    duration = time.time() - start_time
    perf_monitor.record_metric("read_time", duration)
    
    assert len(success_logs) == 1
    assert success_logs[0]["status"] == "success"

def test_log_monitoring(log_manager):
    """Test real-time log monitoring with verification."""
    received_logs = []
    log_received = threading.Event()
    
    def log_observer(log_entry):
        received_logs.append(log_entry)
        log_received.set()
    
    # Add observer
    log_manager.monitor.add_observer(log_observer)
    
    # Write a test log
    log_manager.write_log(
        platform="test_platform",
        status="monitor_test",
        sync=True
    )
    
    # Wait for log reception with timeout
    assert log_received.wait(timeout=1.0)
    assert len(received_logs) == 1
    assert received_logs[0]["status"] == "monitor_test"
    
    # Remove observer
    log_manager.monitor.remove_observer(log_observer)
    
    # Write another log
    log_manager.write_log(
        platform="test_platform",
        status="monitor_test_2",
        sync=True
    )
    
    # Verify observer didn't receive the new log
    assert len(received_logs) == 1

def test_log_metrics(log_manager):
    """Test metrics collection."""
    # Write some test logs
    for i in range(3):
        log_manager.write_log(
            platform="test_platform",
            status=f"test_{i}",
            sync=True
        )
    
    # Get metrics
    metrics = log_manager.get_metrics()
    assert metrics is not None
    assert metrics.total_logs == 3
    assert metrics.total_bytes > 0
    assert metrics.error_count == 0

def test_error_handling(log_manager, temp_log_dir):
    """Test error handling with verification."""
    # Test invalid log directory
    invalid_config = LogConfig(log_dir="/invalid/path")
    with pytest.raises(Exception):
        LogManager(invalid_config)
    
    # Test invalid log data
    log_manager.write_log(
        platform="test_platform",
        status="error_test",
        error="Test error",
        level=LogLevel.ERROR,
        sync=True
    )
    
    log_file = temp_log_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    assert wait_for_file(log_file)
    assert verify_log_content(log_file)

def test_concurrent_writes(log_manager, temp_log_dir, perf_monitor):
    """Test concurrent log writing with performance monitoring."""
    num_threads = 4
    num_writes = 10
    write_complete = threading.Event()
    
    def write_logs():
        for i in range(num_writes):
            log_manager.write_log(
                platform="test_platform",
                status=f"concurrent_test_{i}",
                sync=True
            )
    
    start_time = time.time()
    
    # Create thread pool
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(write_logs) for _ in range(num_threads)]
        for future in futures:
            future.result()
    
    duration = time.time() - start_time
    perf_monitor.record_metric("concurrent_write_time", duration)
    
    # Verify all logs were written
    log_file = temp_log_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    assert wait_for_file(log_file)
    
    with open(log_file) as f:
        logs = json.load(f)
        assert len(logs) == num_threads * num_writes

def pytest_runtest_setup(item):
    """Setup for each test."""
    # Ensure clean state
    LogManager.reset_singleton()

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print performance metrics summary after tests complete."""
    if hasattr(config, "perf_monitor"):
        metrics = config.perf_monitor.get_metrics()
        terminalreporter.write_sep("=", "Performance Metrics Summary")
        for metric_name, stats in metrics.items():
            terminalreporter.write_line(f"\n{metric_name}:")
            terminalreporter.write_line(f"  Min: {stats['min']:.3f}s")
            terminalreporter.write_line(f"  Max: {stats['max']:.3f}s")
            terminalreporter.write_line(f"  Avg: {stats['avg']:.3f}s")
            terminalreporter.write_line(f"  Count: {stats['count']}") 