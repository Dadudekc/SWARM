"""
Test suite for LogBatcher functionality.
"""

import pytest
import time
from datetime import datetime
import tempfile
from pathlib import Path
from threading import Thread
import os
import shutil
from dreamos.social.utils.log_batcher import LogBatcher
from dreamos.core.logging.log_config import LogConfig, LogLevel

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = Path("./test_logs")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield str(temp_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

@pytest.fixture
def log_config(temp_log_dir):
    """Create LogConfig instance with temp directory."""
    return LogConfig(
        log_dir=str(temp_log_dir),
        level=LogLevel.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        retention_days=30,
        max_file_size=1 * 1024 * 1024,
        backup_count=5,
        metrics_enabled=True,
        platforms={"test": "test.log"},
        batch_size=2,
        batch_timeout=1.0,
        max_retries=3,
        retry_delay=0.5
    )

@pytest.fixture
def batcher(log_config):
    """Create test batcher instance."""
    batcher = LogBatcher(
        log_dir=log_config.log_dir,
        batch_size=log_config.batch_size,
        batch_timeout=log_config.batch_timeout
    )
    yield batcher
    batcher.stop()

@pytest.fixture
def test_entry():
    """Create test log entry."""
    return {
        "platform": "test",
        "level": LogLevel.INFO,
        "message": "Test log entry",
        "status": "INFO",
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def test_entries():
    """Create multiple test log entries."""
    return [
        {
            "platform": "test",
            "level": LogLevel.INFO,
            "message": f"Test log entry {i}",
            "status": "INFO",
            "timestamp": datetime.now().isoformat()
        }
        for i in range(5)
    ]

def test_batcher_initialization(log_config):
    """Test LogBatcher initialization."""
    batcher = LogBatcher(
        batch_size=log_config.batch_size,
        batch_timeout=log_config.batch_timeout,
        log_dir=log_config.log_dir
    )
    assert batcher.batch_size == log_config.batch_size
    assert batcher.batch_timeout == log_config.batch_timeout
    assert batcher.is_empty()

def test_add_entry(batcher, test_entry):
    """Test adding a single entry."""
    assert batcher.add_entry(test_entry)
    assert not batcher.is_empty()
    assert len(batcher.get_entries()) == 1

def test_add_entry_after_timeout(batcher):
    """Test adding entry after timeout."""
    entry = {
        "platform": "test",
        "level": LogLevel.INFO,
        "timestamp": "2024-01-01T00:00:00",
        "message": "test message"
    }
    assert batcher.add_entry(entry)
    time.sleep(0.6)  # Wait for timeout
    assert batcher.add_entry(entry)

def test_get_entries(batcher, test_entries):
    """Test getting entries."""
    # Add entries
    for entry in test_entries:
        batcher.add_entry(entry)
    
    # Get first batch (should be batch_size entries)
    entries = batcher.get_entries()
    assert len(entries) == batcher.batch_size, f"Expected {batcher.batch_size} entries, got {len(entries)}"
    
    # Get second batch (should be batch_size entries)
    entries = batcher.get_entries()
    assert len(entries) == batcher.batch_size, f"Expected {batcher.batch_size} entries, got {len(entries)}"
    
    # Get remaining entries
    entries = batcher.get_entries()
    assert len(entries) == len(test_entries) - (2 * batcher.batch_size), f"Expected {len(test_entries) - (2 * batcher.batch_size)} entries, got {len(entries)}"
    assert batcher.is_empty(), "Batcher should be empty after getting all entries"

def test_add_entries_until_full(batcher):
    """Test adding entries until batch is full."""
    entry = {
        "platform": "test",
        "level": LogLevel.INFO,
        "timestamp": "2024-01-01T00:00:00",
        "message": "test message"
    }
    for _ in range(2):
        assert batcher.add_entry(entry)
    assert not batcher.add_entry(entry)

def test_concurrent_access(batcher):
    """Test concurrent access to batcher."""
    def add_entries():
        entry = {
            "platform": "test",
            "level": LogLevel.INFO,
            "timestamp": "2024-01-01T00:00:00",
            "message": "test message"
        }
        entries_added = 0
        while entries_added < 20:
            if batcher.add_entry(entry):
                entries_added += 1
            else:
                # If batch is full, flush it
                batcher.flush()
                time.sleep(0.01)  # Small delay to prevent CPU spinning
    
    # Create and start threads
    threads = [Thread(target=add_entries) for _ in range(5)]
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Wait a bit for any pending operations
    time.sleep(0.2)  # Increased wait time
    
    # Force final flush
    batcher.flush()
    
    # Collect all entries
    total_entries = 0
    while not batcher.is_empty():
        entries = batcher.get_entries()
        total_entries += len(entries)
        time.sleep(0.01)  # Give other threads a chance to add entries
    
    # Verify total entries
    expected_entries = 5 * 20  # 5 threads * 20 entries each
    assert total_entries == expected_entries, f"Expected {expected_entries} entries, got {total_entries}" 
