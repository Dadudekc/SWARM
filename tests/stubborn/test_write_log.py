"""
Test log writing functionality with Windows-specific fixes.
"""

import os
import json
import pytest
from pathlib import Path
from typing import Dict, Any
from contextlib import contextmanager

# Minimal Windows-specific utilities
def normalize_path(path: str) -> Path:
    """Normalize path for Windows compatibility."""
    return Path(path).resolve()

@contextmanager
def safe_file_handle(filepath: str, mode: str = 'r', encoding: str = 'utf-8'):
    """Safe file handle with proper cleanup."""
    filepath = normalize_path(filepath)
    handle = None
    try:
        handle = open(filepath, mode, encoding=encoding)
        yield handle
    finally:
        if handle:
            handle.close()

def test_write_log():
    """Test basic log writing with proper file handle management."""
    log_file = "test_log.json"
    test_data = {"message": "test log entry", "level": "INFO"}
    
    # Write with safe file handle
    with safe_file_handle(log_file, 'w') as f:
        json.dump(test_data, f)
    
    # Verify write
    with safe_file_handle(log_file, 'r') as f:
        written_data = json.load(f)
        assert written_data == test_data
    
    # Cleanup
    try:
        os.remove(log_file)
    except PermissionError:
        # Windows-specific: wait for file handle to be released
        import time
        time.sleep(0.1)
        os.remove(log_file)

def test_write_log_batch():
    """Test batch log writing with proper file handle management."""
    log_file = "test_batch_log.json"
    test_entries = [
        {"message": f"test entry {i}", "level": "INFO"}
        for i in range(3)
    ]
    
    # Write batch with safe file handle
    with safe_file_handle(log_file, 'w') as f:
        json.dump(test_entries, f)
    
    # Verify batch write
    with safe_file_handle(log_file, 'r') as f:
        written_entries = json.load(f)
        assert written_entries == test_entries
    
    # Cleanup
    try:
        os.remove(log_file)
    except PermissionError:
        import time
        time.sleep(0.1)
        os.remove(log_file)

def test_write_log_encoding():
    """Test log writing with proper encoding handling."""
    log_file = "test_encoding_log.json"
    test_data = {"message": "test log entry with special chars: é, ñ, 漢字", "level": "INFO"}
    
    # Write with explicit UTF-8 encoding
    with safe_file_handle(log_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False)
    
    # Verify write with same encoding
    with safe_file_handle(log_file, 'r', encoding='utf-8') as f:
        written_data = json.load(f)
        assert written_data == test_data
    
    # Cleanup
    try:
        os.remove(log_file)
    except PermissionError:
        import time
        time.sleep(0.1)
        os.remove(log_file)

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup test files after each test."""
    yield
    for file in ["test_log.json", "test_batch_log.json", "test_encoding_log.json"]:
        try:
            if os.path.exists(file):
                os.remove(file)
        except PermissionError:
            import time
            time.sleep(0.1)
            if os.path.exists(file):
                os.remove(file) 
