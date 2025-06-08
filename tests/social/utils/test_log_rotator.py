"""Tests for the LogRotator component."""

import pytest
from pathlib import Path
import json
from datetime import datetime, timedelta
import time
import os

from dreamos.social.utils.log_rotator import LogRotator
from dreamos.core.logging.log_config import LogConfig, LogLevel

@pytest.fixture
def test_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

@pytest.fixture
def log_config(test_log_dir):
    """Create a test log configuration."""
    return LogConfig(
        log_dir=str(test_log_dir),
        level=LogLevel.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        retention_days=30,
        max_file_size=1 * 1024 * 1024,
        backup_count=3,
        metrics_enabled=True,
        platforms={"test": "test.log"},
        batch_size=10,
        batch_timeout=1.0,
        max_retries=3,
        retry_delay=0.5
    )

@pytest.fixture
def log_rotator(log_config):
    """Create a test log rotator instance."""
    return LogRotator(config=log_config)

def test_log_rotator_initialization(log_rotator, test_log_dir, log_config):
    """Test LogRotator initialization."""
    assert log_rotator.log_dir == test_log_dir
    assert log_rotator.config.retention_days == log_config.retention_days
    assert log_rotator.config.max_file_size == log_config.max_file_size
    assert log_rotator.config.backup_count == log_config.backup_count

def test_rotate_large_file(log_rotator, test_log_dir):
    """Test rotating a file that exceeds max size."""
    # Create a large log file
    log_file = test_log_dir / "test_operations.json"
    with open(log_file, "w") as f:
        for i in range(1000):  # Write enough to exceed 1KB
            f.write(json.dumps({"message": "x" * 100}) + "\n")
    
    # Use a small max_file_size to force rotation
    config = LogConfig(
        log_dir=str(test_log_dir),
        level=LogLevel.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        retention_days=30,
        max_file_size=1024,  # 1KB
        backup_count=3,
        metrics_enabled=True,
        platforms={"test": "test.log"},
        batch_size=10,
        batch_timeout=1.0,
        max_retries=3,
        retry_delay=0.5
    )
    rotator = LogRotator(config=config)
    rotated_path = rotator.rotate_if_needed(str(log_file))
    
    # Check for rotated file
    assert rotated_path is not None
    assert os.path.exists(rotated_path), "Rotated file was not created"
    assert log_file.exists(), "Original file should exist (new empty log created after rotation)"
    assert os.path.getsize(log_file) == 0, "Original file should be empty after rotation"
    assert os.path.getsize(rotated_path) > 0, "Rotated file should contain the old log data"

def test_compress_old_file(log_rotator, test_log_dir):
    """Test compressing old log files."""
    # Create an old log file
    log_file = test_log_dir / "test_operations_20230101.json"
    log_file.write_text("Test content")
    
    # Set file modification time to be old enough for compression
    old_time = datetime.now() - timedelta(days=2)
    log_file.touch(exist_ok=True)
    os.utime(log_file, (old_time.timestamp(), old_time.timestamp()))
    
    # Trigger compression
    log_rotator.compress_if_needed(str(log_file))
    
    # Check for compressed file
    compressed_file = log_file.with_suffix(log_file.suffix + ".gz")
    assert compressed_file.exists()
    assert not log_file.exists()

def test_cleanup_old_files(log_rotator, test_log_dir):
    """Test cleaning up old log files."""
    # Create old log files
    old_files = []
    for i in range(5):  # Create more than max_files
        file = test_log_dir / f"old_{i}.json"
        file.write_text("Old content")
        old_time = datetime.now() - timedelta(days=8)
        file.touch(exist_ok=True)
        os.utime(file, (old_time.timestamp(), old_time.timestamp()))
        old_files.append(file)
    
    # Run cleanup
    log_rotator.cleanup()
    
    # Check that only max_files files remain
    remaining_files = list(test_log_dir.glob("*.json"))
    assert len(remaining_files) <= log_rotator.config.backup_count

def test_do_not_rotate_small_file(log_rotator, test_log_dir):
    """Test that small files are not rotated."""
    # Create a small log file
    log_file = test_log_dir / "test_operations.json"
    log_file.write_text("Small content")
    
    # Try to rotate
    rotated_path = log_rotator.rotate_if_needed(str(log_file))
    
    # Check that file wasn't rotated
    assert rotated_path is None
    assert log_file.exists()
    rotated_files = list(test_log_dir.glob("test_operations_*.json"))
    assert len(rotated_files) == 0

def test_do_not_compress_new_file(log_rotator, test_log_dir):
    """Test that new files are not compressed."""
    # Create a new log file
    log_file = test_log_dir / "test_operations_20230101.json"
    log_file.write_text("New content")
    
    # Try to compress
    log_rotator.compress_if_needed(str(log_file))
    
    # Check that file wasn't compressed
    assert log_file.exists()
    compressed_file = log_file.with_suffix(log_file.suffix + ".gz")
    assert not compressed_file.exists() 
