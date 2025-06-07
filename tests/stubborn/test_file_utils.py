"""Tests for the file_utils module."""

import pytest
import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
import sys

from dreamos.core.utils.file_utils import (
    ensure_dir, safe_write, safe_read,
    read_json, write_json, load_yaml, save_yaml,
    find_files, cleanup_old_files
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

def test_safe_write(temp_dir):
    """Test safe file writing."""
    test_file = temp_dir / "test.txt"
    content = "test content"
    
    # Test writing new file
    assert safe_write(test_file, content)
    assert test_file.read_text() == content
    
    # Test writing with backup
    new_content = "new content"
    assert safe_write(test_file, new_content, backup=True)
    assert test_file.read_text() == new_content
    assert test_file.with_suffix('.txt.bak').exists()
    assert test_file.with_suffix('.txt.bak').read_text() == content
    
    # Test writing to read-only location
    if os.name == 'nt':  # Windows
        import win32api
        import win32con
        win32api.SetFileAttributes(str(test_file), win32con.FILE_ATTRIBUTE_READONLY)
    else:  # Unix
        os.chmod(test_file, 0o444)
    
    try:
        assert not safe_write(test_file, "should fail")
    finally:
        # Restore permissions
        if os.name == 'nt':
            win32api.SetFileAttributes(str(test_file), win32con.FILE_ATTRIBUTE_NORMAL)
        else:
            os.chmod(test_file, 0o644)

def test_safe_read(temp_dir):
    """Test safe file reading."""
    test_file = temp_dir / "test.txt"
    content = "test content"
    test_file.write_text(content)
    
    # Test reading existing file
    assert safe_read(test_file) == content
    
    # Test reading non-existent file
    assert safe_read(temp_dir / "nonexistent.txt", default="default") == "default"
    
    # Test reading with different encoding
    test_file.write_text("test content", encoding='utf-16')
    assert safe_read(test_file, encoding='utf-16') == "test content"

def test_load_save_json(temp_dir, sample_data):
    """Test JSON loading and saving."""
    test_file = temp_dir / "test.json"
    
    # Test saving
    assert save_json(sample_data, test_file)
    assert test_file.exists()
    
    # Test loading
    loaded_data = read_json(test_file)
    assert loaded_data == sample_data
    
    # Test loading non-existent file
    assert read_json(temp_dir / "nonexistent.json", default={}) == {}
    
    # Test loading invalid JSON
    test_file.write_text("invalid json")
    assert read_json(test_file, default={}) == {}

def test_load_save_yaml(temp_dir, sample_data):
    """Test YAML loading and saving."""
    test_file = temp_dir / "test.yaml"
    
    # Test saving
    assert save_yaml(sample_data, test_file)
    assert test_file.exists()
    
    # Test loading
    loaded_data = load_yaml(test_file)
    assert loaded_data == sample_data
    
    # Test loading non-existent file
    assert load_yaml(temp_dir / "nonexistent.yaml", default={}) == {}
    
    # Test loading invalid YAML
    test_file.write_text("invalid: yaml: content:")
    assert load_yaml(test_file, default={}) == {}

def test_find_files(temp_dir):
    """Test file finding functionality."""
    # Create test directory structure
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir2").mkdir()
    (temp_dir / "dir1" / "test1.txt").write_text("test1")
    (temp_dir / "dir1" / "test2.txt").write_text("test2")
    (temp_dir / "dir2" / "test3.txt").write_text("test3")
    
    # Test finding all files
    files = find_files(temp_dir, "*.txt")
    assert len(files) == 3
    
    # Test finding files in specific directory
    files = find_files(temp_dir / "dir1", "*.txt")
    assert len(files) == 2
    
    # Test finding files non-recursively
    files = find_files(temp_dir, "*.txt", recursive=False)
    assert len(files) == 0  # No files in root directory
    
    # Test finding with pattern
    files = find_files(temp_dir, "test1.txt")
    assert len(files) == 1
    assert files[0].name == "test1.txt"

def test_cleanup_old_files(temp_dir):
    """Test cleanup of old files."""
    # Create test files with different ages
    now = datetime.now()
    old_date = now - timedelta(days=31)
    
    # Create old file
    old_file = temp_dir / "old.txt"
    old_file.write_text("old content")
    os.utime(old_file, (old_date.timestamp(), old_date.timestamp()))
    
    # Create new file
    new_file = temp_dir / "new.txt"
    new_file.write_text("new content")
    
    # Test cleanup
    cleaned = cleanup_old_files(temp_dir, max_age_days=30)
    assert cleaned == 1
    assert not old_file.exists()
    assert new_file.exists()

# Error Handling Tests

def test_safe_write_errors(temp_dir):
    """Test error handling in safe_write."""
    # Test writing with invalid mode
    test_file = temp_dir / "test.txt"
    assert not safe_write(test_file, "content", mode="invalid")

def test_safe_read_errors(temp_dir):
    """Test error handling in safe_read."""
    # Test reading with invalid mode
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert safe_read(test_file, mode="invalid", default="default") == "default"

def test_json_errors(temp_dir):
    """Test error handling in JSON operations."""
    test_file = temp_dir / "test.json"
    
    # Test saving invalid data
    class InvalidData:
        pass
    
    assert not save_json(InvalidData(), test_file)
    
    # Test loading invalid JSON
    test_file.write_text("invalid json")
    assert read_json(test_file, default={}) == {}

def test_yaml_errors(temp_dir):
    """Test error handling in YAML operations."""
    test_file = temp_dir / "test.yaml"
    # Test saving invalid data (use a function, which is not serializable)
    def not_serializable():
        pass
    assert not save_yaml(not_serializable, test_file)
    # Test loading invalid YAML
    test_file.write_text("invalid: yaml: content:")
    assert load_yaml(test_file, default={}) == {}

@pytest.mark.skipif(sys.platform.startswith('win'), reason="Permission errors unreliable on Windows")
def test_ensure_dir_permissions(temp_dir):
    """Test directory creation with permission issues."""
    os.chmod(temp_dir, 0o444)
    try:
        with pytest.raises(PermissionError):
            ensure_dir(temp_dir / "should_fail")
    finally:
        os.chmod(temp_dir, 0o755)

# Cross-Platform Tests

@pytest.mark.parametrize("path", [
    "test.txt",
    "subdir/test.txt",
    "subdir/with/spaces/test.txt",
    "subdir/with/special/chars/!@#$%/test.txt"
])
def test_cross_platform_paths(temp_dir, path):
    """Test handling of various path formats."""
    full_path = temp_dir / path
    content = "test content"
    
    # Test writing
    assert safe_write(full_path, content)
    assert full_path.exists()
    
    # Test reading
    assert safe_read(full_path) == content 