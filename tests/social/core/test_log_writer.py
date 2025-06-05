"""
Log Writer Test Suite
--------------------
Tests for the LogWriter functionality:
- File writing operations
- Error handling
- Encoding safety
- File I/O operations
- Batch processing operations
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, ANY, MagicMock
import json
import os
import stat
import win32security
import ntsecuritycon as con
from typing import List, Dict, Any
from contextlib import contextmanager

from social.utils.log_writer import LogWriter, LogEntry
from social.utils.log_config import LogConfig, LogLevel

# --- Merged from test_batch_processing.py on 2025-06-05 ---
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
# --- End of merged code ---

@pytest.fixture
def test_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    yield log_dir
    # Cleanup
    try:
        for file in log_dir.glob("*"):
            file.unlink()
        log_dir.rmdir()
    except Exception as e:
        print(f"Warning: Failed to cleanup test directory: {e}")

@pytest.fixture
def test_config():
    """Create a test configuration."""
    return LogConfig(
        log_dir="test_logs",
        level=LogLevel.INFO,
        platforms={"test": "test.log"},
        max_size_mb=10,
        batch_size=100,
        output_format="json"
    )

@pytest.fixture
def log_writer(test_log_dir, test_config):
    """Create a LogWriter instance with test directory."""
    writer = LogWriter(test_log_dir, test_config)
    yield writer
    # Cleanup
    try:
        writer._cleanup_all_locks()
    except Exception as e:
        print(f"Warning: Failed to cleanup log writer: {e}")

@pytest.fixture
def sample_log_entry():
    """Create a sample log entry for testing."""
    return {
        "timestamp": datetime.now(),
        "platform": "test_platform",
        "status": "success",
        "message": "Test log message",
        "level": LogLevel.INFO.value
    }

class TestLogWriter:
    """Test suite for LogWriter functionality."""
    
    def test_initialization(self, test_log_dir, test_config):
        """Test LogWriter initialization."""
        writer = LogWriter(test_log_dir, test_config)
        assert writer.log_dir == test_log_dir
        assert isinstance(writer.log_dir, Path)
    
    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_log_json(self, mock_exists, mock_file, mock_json_dump, log_writer, sample_log_entry):
        """Test writing a log entry in JSON format."""
        platform = sample_log_entry["platform"]
        log_file = log_writer.log_dir / f"{platform}_operations.json"
        
        # Mock file operations
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = "[]"
        
        # Write log
        log_writer.write_log(sample_log_entry)
        
        # Verify file operations
        mock_file.assert_called_with(log_file, 'w', encoding='utf-8')
        
        # Verify JSON dump
        mock_json_dump.assert_called_once()
        dumped_data = mock_json_dump.call_args[0][0]
        assert len(dumped_data) == 1
        assert dumped_data[0]["platform"] == platform
        assert dumped_data[0]["message"] == sample_log_entry["message"]
    
    @patch("builtins.open", new_callable=mock_open)
    def test_write_log_text(self, mock_file, log_writer, sample_log_entry):
        """Test writing a log entry in text format."""
        platform = sample_log_entry["platform"]
        log_file = log_writer.log_dir / f"{platform}.log"
        
        log_writer.write_log(sample_log_entry, format="text")
        
        # Verify file operations
        mock_file.assert_called_with(log_file, 'a', encoding='utf-8')
        
        # Verify text content
        written_text = mock_file().write.call_args[0][0]
        assert sample_log_entry["message"] in written_text
        assert str(sample_log_entry["level"]) in written_text
    
    def test_write_log_error_handling(self, log_writer, sample_log_entry):
        """Test error handling during log writing."""
        with patch('builtins.open', side_effect=IOError("Test error")):
            # Should not raise exception
            log_writer.write_log(sample_log_entry)
    
    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_log_encoding(self, mock_exists, mock_file, mock_json_dump, log_writer):
        """Test writing log entries with special characters."""
        entry = {
            "timestamp": datetime.now(),
            "platform": "test_platform",
            "status": "success",
            "message": "Test message with special chars: é, ñ, 漢字",
            "level": LogLevel.INFO.value
        }
        
        # Mock file operations
        mock_file.return_value.__enter__.return_value.read.return_value = "[]"
        mock_exists.return_value = True
        
        log_writer.write_log(entry)
        
        # Verify JSON dump
        mock_json_dump.assert_called_once()
        dumped_data = mock_json_dump.call_args[0][0]
        assert dumped_data[0]["message"] == entry["message"]
    
    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_log_file_creation(self, mock_exists, mock_file, mock_json_dump, log_writer, sample_log_entry):
        """Test that log files are created if they don't exist."""
        platform = sample_log_entry["platform"]
        log_file = log_writer.log_dir / f"{platform}_operations.json"
        
        # Mock file operations for new file
        mock_exists.return_value = False
        mock_file.return_value.__enter__.return_value.read.return_value = "[]"
        
        # Write log
        log_writer.write_log(sample_log_entry)
        
        # Verify file operations
        mock_file.assert_called_with(log_file, 'w', encoding='utf-8')
        
        # Verify JSON dump
        mock_json_dump.assert_called_once()
        dumped_data = mock_json_dump.call_args[0][0]
        assert len(dumped_data) == 1
        assert dumped_data[0]["platform"] == platform

    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_multiple_entries(self, mock_exists, mock_file, mock_json_dump, log_writer, test_log_dir):
        """Test writing multiple log entries."""
        entries = [
            {
                "timestamp": datetime.now(),
                "platform": "test",
                "status": "success",
                "message": f"Message {i}",
                "level": LogLevel.INFO.value
            }
            for i in range(3)
        ]
        
        # Mock file operations
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = "[]"
        
        # Write logs
        for entry in entries:
            log_writer.write_log(entry)
        
        # Verify JSON dump
        mock_json_dump.assert_called()
        dumped_data = mock_json_dump.call_args[0][0]
        assert len(dumped_data) == 3
        for i, entry in enumerate(dumped_data):
            assert entry["message"] == f"Message {i}"

    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_entry_with_metadata(self, mock_exists, mock_file, mock_json_dump, log_writer):
        """Test writing a log entry with additional metadata."""
        entry = {
            "timestamp": datetime.now(),
            "platform": "test",
            "status": "success",
            "message": "Test message",
            "level": LogLevel.INFO.value,
            "metadata": {"user_id": "123", "action": "login"}
        }
        
        # Mock file operations
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value.read.return_value = "[]"
        
        log_writer.write_log(entry)
        
        # Verify JSON dump
        mock_json_dump.assert_called_once()
        dumped_data = mock_json_dump.call_args[0][0]
        assert dumped_data[0]["metadata"]["user_id"] == "123"
        assert dumped_data[0]["metadata"]["action"] == "login"

    @patch("social.utils.log_writer.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_write_entry_permission_error(self, mock_exists, mock_file, mock_json_dump, log_writer):
        """Test error handling when writing entries with permission issues."""
        entry = {
            "timestamp": datetime.now(),
            "platform": "test",
            "status": "success",
            "message": "Test message",
            "level": LogLevel.INFO.value
        }
        
        # Mock file operations to simulate permission error
        mock_file.side_effect = PermissionError("Access denied")
        
        with pytest.raises(PermissionError):
            log_writer.write_log(entry)

class TestBatchProcessing:
    """Test suite for batch log processing functionality."""
    
    def test_batch_processing(self, test_log_dir):
        """Test batch log processing with proper file handle management."""
        log_file = test_log_dir / "test_batch_process.json"
        test_entries = [
            {"message": f"batch entry {i}", "level": "INFO", "timestamp": f"2024-03-{i:02d}"}
            for i in range(1, 4)
        ]
        
        # Write batch entries
        with safe_file_handle(str(log_file), 'w') as f:
            json.dump(test_entries, f)
        
        # Process batch entries
        processed_entries = []
        with safe_file_handle(str(log_file), 'r') as f:
            entries = json.load(f)
            for entry in entries:
                processed_entries.append({
                    **entry,
                    "processed": True,
                    "batch_id": "test_batch"
                })
        
        # Write processed entries
        with safe_file_handle(str(log_file), 'w') as f:
            json.dump(processed_entries, f)
        
        # Verify processing
        with safe_file_handle(str(log_file), 'r') as f:
            final_entries = json.load(f)
            assert len(final_entries) == 3
            assert all(entry["processed"] for entry in final_entries)
            assert all(entry["batch_id"] == "test_batch" for entry in final_entries)
    
    def test_batch_processing_large(self, test_log_dir):
        """Test batch processing with larger dataset."""
        log_file = test_log_dir / "test_batch_large.json"
        test_entries = [
            {"message": f"large batch entry {i}", "level": "INFO", "data": "x" * 100}
            for i in range(100)
        ]
        
        # Write large batch
        with safe_file_handle(str(log_file), 'w') as f:
            json.dump(test_entries, f)
        
        # Process in chunks
        chunk_size = 20
        processed_entries = []
        
        with safe_file_handle(str(log_file), 'r') as f:
            entries = json.load(f)
            for i in range(0, len(entries), chunk_size):
                chunk = entries[i:i + chunk_size]
                processed_entries.extend([
                    {**entry, "processed": True, "chunk": i // chunk_size}
                    for entry in chunk
                ])
        
        # Write processed chunks
        with safe_file_handle(str(log_file), 'w') as f:
            json.dump(processed_entries, f)
        
        # Verify processing
        with safe_file_handle(str(log_file), 'r') as f:
            final_entries = json.load(f)
            assert len(final_entries) == 100
            assert all(entry["processed"] for entry in final_entries)
            assert len(set(entry["chunk"] for entry in final_entries)) == 5 