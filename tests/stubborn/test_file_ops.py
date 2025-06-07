"""Tests for file utilities."""

import os
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

from dreamos.core.utils.file_utils import (
    ensure_dir,
    safe_write,
    safe_read,
    atomic_write,
    backup_file,
    restore_backup,
    read_json,
    write_json,
    read_yaml,
    write_yaml,
    safe_rmdir,
    safe_file_handle,
    rotate_file,
    FileOpsError,
    FileOpsPermissionError,
    FileOpsIOError
)
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel

# Initialize logging
log_manager = LogManager(LogConfig(
    level=LogLevel.DEBUG,
    log_dir="logs/tests/file_ops",
    platforms={"test": "file_ops.log"}
))
logger = log_manager

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path

@pytest.fixture
def test_data():
    """Sample test data."""
    return {
        'string': 'test',
        'number': 42,
        'list': [1, 2, 3],
        'dict': {'key': 'value'}
    }

def test_safe_file_handle(temp_dir):
    """Test safe file handle context manager."""
    test_file = temp_dir / 'test.txt'
    
    # Test write
    with safe_file_handle(test_file, 'w') as f:
        f.write('test')
    assert test_file.exists()
    
    # Test read
    with safe_file_handle(test_file, 'r') as f:
        content = f.read()
    assert content == 'test'
    
    # Test error handling
    with pytest.raises(FileOpsIOError):
        with safe_file_handle(test_file / 'nonexistent' / 'file.txt', 'r'):
            pass

def test_ensure_dir(temp_dir):
    """Test directory creation and permissions."""
    test_dir = temp_dir / 'test' / 'subdir'
    
    # Test creation
    created = ensure_dir(test_dir)
    assert created.exists()
    assert created.is_dir()
    
    # Test existing directory
    ensure_dir(test_dir)  # Should not raise
    
    # Test permissions (Unix only)
    if os.name != 'nt':
        assert oct(created.stat().st_mode)[-3:] == '755'

def test_safe_rmdir(temp_dir):
    """Test directory removal."""
    test_dir = temp_dir / 'test'
    ensure_dir(test_dir)
    
    # Test simple removal
    safe_rmdir(test_dir)
    assert not test_dir.exists()
    
    # Test recursive removal
    subdir = test_dir / 'subdir'
    ensure_dir(subdir)
    (subdir / 'file.txt').write_text('test')
    safe_rmdir(test_dir, recursive=True)
    assert not test_dir.exists()

def test_json_operations(temp_dir, test_data):
    """Test JSON read/write operations."""
    test_file = temp_dir / 'test.json'
    
    # Test write
    write_json(test_file, test_data)
    assert test_file.exists()
    
    # Test read
    data = read_json(test_file)
    assert data == test_data
    
    # Test default value
    data = read_json(temp_dir / 'nonexistent.json', default={})
    assert data == {}
    
    # Test invalid JSON
    test_file.write_text('invalid json')
    data = read_json(test_file, default={})
    assert data == {}

def test_yaml_operations(temp_dir, test_data):
    """Test YAML read/write operations."""
    test_file = temp_dir / 'test.yaml'
    
    # Test write
    write_yaml(test_file, test_data)
    assert test_file.exists()
    
    # Test read
    data = read_yaml(test_file)
    assert data == test_data
    
    # Test default value
    data = read_yaml(temp_dir / 'nonexistent.yaml', default={})
    assert data == {}
    
    # Test invalid YAML
    test_file.write_text('invalid: yaml: :')
    data = read_yaml(test_file, default={})
    assert data == {}

def test_rotate_file(temp_dir):
    """Test file rotation."""
    test_file = temp_dir / 'test.log'
    
    # Create initial file
    test_file.write_text('x' * 11 * 1024 * 1024)  # 11MB
    
    # Test rotation
    rotate_file(test_file, max_size=10 * 1024 * 1024, max_files=3)
    
    # Check rotated files
    assert not test_file.exists()  # File should be gone after rotation
    assert (test_file.with_suffix('.1')).exists()
    
    # Test max files limit
    for i in range(4):
        test_file.write_text('x' * 11 * 1024 * 1024)
        rotate_file(test_file, max_size=10 * 1024 * 1024, max_files=3)
    
    assert not (test_file.with_suffix('.4')).exists()
    assert (test_file.with_suffix('.3')).exists()

def test_safe_write_read(temp_dir):
    """Test safe write and read operations."""
    test_file = temp_dir / 'test.txt'
    test_content = 'test content'
    
    # Test write
    safe_write(test_file, test_content)
    assert test_file.exists()
    
    # Test read
    content = safe_read(test_file)
    assert content == test_content
    
    # Test read non-existent file
    content = safe_read(temp_dir / 'nonexistent.txt', default='default')
    assert content == 'default'

def test_permission_errors(temp_dir):
    """Test permission error handling."""
    test_file = temp_dir / 'test.txt'
    test_file.write_text('test')
    
    # Make file read-only
    if os.name != 'nt':
        os.chmod(test_file, 0o444)
        
        with pytest.raises(FileOpsPermissionError):
            safe_write(test_file, 'test')
            
        with pytest.raises(FileOpsPermissionError):
            write_json(test_file, {'test': 'data'}) 