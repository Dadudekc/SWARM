"""Tests for file operations."""

import pytest
import os
import json
import yaml
import stat
from pathlib import Path
from unittest.mock import patch, mock_open
import tempfile
import shutil
from platform import system as is_windows

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
    safe_mkdir,
    safe_remove,
    safe_copy,
    safe_move,
    safe_file_handle,
    rotate_file,
    FileOpsError,
    FileOpsPermissionError,
    FileOpsIOError
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "string": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {
            "key": "value"
        }
    }

# Basic Functionality Tests

def test_read_write_json(temp_dir, sample_data):
    """Test reading and writing JSON files."""
    path = temp_dir / "test.json"
    
    # Test writing
    write_json(path, sample_data)
    assert path.exists()
    
    # Test reading
    loaded_data = read_json(path)
    assert loaded_data == sample_data
    
    # Test default value
    assert read_json(temp_dir / "nonexistent.json", default={}) == {}

def test_read_write_yaml(temp_dir, sample_data):
    """Test reading and writing YAML files."""
    path = temp_dir / "test.yaml"
    
    # Test writing
    write_yaml(path, sample_data)
    assert path.exists()
    
    # Test reading
    loaded_data = read_yaml(path)
    assert loaded_data == sample_data
    
    # Test default value
    assert read_yaml(temp_dir / "nonexistent.yaml", default={}) == {}

def test_ensure_dir(temp_dir):
    """Test directory creation."""
    # Test single directory
    new_dir = temp_dir / "subdir"
    ensure_dir(new_dir)
    assert new_dir.exists() and new_dir.is_dir()
    
    # Test nested directories
    nested_dir = temp_dir / "nested" / "subdir" / "deep"
    ensure_dir(nested_dir)
    assert nested_dir.exists() and nested_dir.is_dir()
    
    # Test existing directory (should not raise)
    ensure_dir(new_dir)

def test_safe_rmdir(temp_dir):
    """Test safe directory removal."""
    # Test removing empty directory
    test_dir = temp_dir / "empty_dir"
    test_dir.mkdir()
    safe_rmdir(test_dir)
    assert not test_dir.exists()
    
    # Test removing directory with files
    test_dir = temp_dir / "dir_with_files"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("test")
    safe_rmdir(test_dir, recursive=True)
    assert not test_dir.exists()
    
    # Test removing non-existent directory (should not raise)
    safe_rmdir(temp_dir / "nonexistent")

def test_rotate_file(temp_dir):
    """Test file rotation functionality."""
    test_file = temp_dir / "rotate.log"
    test_file.write_text("test content")
    
    # On Windows, we need to ensure file handles are closed
    if is_windows():
        import time
        time.sleep(0.1)  # Small delay to ensure file handles are closed
    
    # Rotate the file
    rotate_file(test_file)
    
    # On Windows, we need to ensure file handles are closed
    if is_windows():
        time.sleep(0.1)  # Small delay to ensure file handles are closed
    
    # Check that the original file exists and is empty
    assert test_file.exists()
    assert test_file.read_text() == ""
    
    # Check that the rotated file exists with original content
    rotated_file = test_file.with_suffix('.1')
    assert rotated_file.exists()
    assert rotated_file.read_text() == "test content"
    
    # Test multiple rotations
    test_file.write_text("new content")
    
    # On Windows, we need to ensure file handles are closed
    if is_windows():
        time.sleep(0.1)  # Small delay to ensure file handles are closed
    
    rotate_file(test_file)
    
    # On Windows, we need to ensure file handles are closed
    if is_windows():
        time.sleep(0.1)  # Small delay to ensure file handles are closed
    
    # Check that the original file is empty again
    assert test_file.exists()
    assert test_file.read_text() == ""
    
    # Check that the rotated files have the correct content
    assert rotated_file.exists()
    assert rotated_file.read_text() == "new content"
    
    # Check that the old rotated file was moved to .2
    old_rotated = test_file.with_suffix('.2')
    assert old_rotated.exists()
    assert old_rotated.read_text() == "test content"

def test_safe_file_handle(temp_dir):
    """Test safe file handle context manager."""
    path = temp_dir / "test.txt"
    
    # Test writing
    with safe_file_handle(path, 'w') as f:
        f.write("test")
    assert path.read_text() == "test"
    
    # Test reading
    with safe_file_handle(path, 'r') as f:
        content = f.read()
    assert content == "test"

# Failure Condition Tests

def test_read_nonexistent_file(temp_dir):
    """Test reading from a non-existent file raises FileOpsError."""
    nonexistent_file = temp_dir / "nonexistent.json"
    with pytest.raises(FileOpsError):
        read_json(nonexistent_file)

def test_invalid_json(temp_dir):
    """Test reading invalid JSON raises FileOpsIOError."""
    invalid_file = temp_dir / "invalid.json"
    invalid_file.write_text("invalid json content")
    
    with pytest.raises(FileOpsIOError):
        read_json(invalid_file)

def test_invalid_yaml(temp_dir):
    """Test reading invalid YAML raises FileOpsIOError."""
    invalid_file = temp_dir / "invalid.yaml"
    invalid_file.write_text("foo: [unclosed")  # This is definitely invalid YAML syntax
    
    with pytest.raises(FileOpsIOError) as exc_info:
        read_yaml(invalid_file)
    assert "Invalid YAML" in str(exc_info.value)

def test_rotate_nonexistent_file(temp_dir):
    """Test rotating non-existent file raises FileOpsError."""
    with pytest.raises(FileOpsError):
        rotate_file(temp_dir / "nonexistent.log")

def test_safe_rmdir_nonexistent(temp_dir):
    """Test removing a non-existent directory does not raise an error."""
    nonexistent_dir = temp_dir / "nonexistent"
    safe_rmdir(nonexistent_dir)  # Should not raise
    assert not nonexistent_dir.exists()

def test_safe_rmdir_nonempty_without_recursive(temp_dir):
    """Test removing non-empty directory without recursive flag raises error."""
    path = temp_dir / "nonempty"
    path.mkdir()
    (path / "test.txt").write_text("test")
    
    with pytest.raises(FileOpsError):
        safe_rmdir(path, recursive=False)

# Cross-Platform Tests

@pytest.mark.parametrize("path", [
    "test.json",
    "subdir/test.json",
    "subdir/with/spaces/test.json",
    "subdir/with/special/chars/!@#$%/test.json"
])
def test_cross_platform_paths(temp_dir, path):
    """Test handling of various path formats."""
    full_path = temp_dir / path
    data = {"key": "value"}
    
    # Test JSON
    write_json(full_path, data)
    assert read_json(full_path) == data
    
    # Test YAML
    yaml_path = full_path.with_suffix('.yaml')
    write_yaml(yaml_path, data)
    assert read_yaml(yaml_path) == data

def test_file_ops_error_hierarchy():
    """Test error class hierarchy."""
    assert issubclass(FileOpsPermissionError, FileOpsError)
    assert issubclass(FileOpsIOError, FileOpsError) 