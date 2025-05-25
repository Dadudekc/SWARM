import os
import json
import gzip
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from dreamos.social.log_writer import (
    setup_logging,
    rotate_logs,
    write_json_log,
    read_logs,
    LOGS_DIR,
    MAX_LOG_SIZE,
    MAX_LOG_AGE,
    COMPRESS_AFTER
)

@pytest.fixture
def mock_logs_dir(tmp_path):
    """Create a temporary directory for logs."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    # Override LOGS_DIR for testing
    import social.log_writer
    social.log_writer.LOGS_DIR = str(logs_dir)
    return logs_dir

def test_setup_logging(mock_logs_dir):
    """Test logging setup."""
    setup_logging()
    assert os.path.exists(mock_logs_dir)

def test_write_json_log(mock_logs_dir):
    """Test basic log writing."""
    write_json_log(
        platform="test_platform",
        status="test_status",
        tags=["test"],
        metadata={"test": "data"}
    )
    
    log_file = mock_logs_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    assert log_file.exists()
    
    with open(log_file) as f:
        logs = json.load(f)
        assert len(logs) == 1
        assert logs[0]["platform"] == "test_platform"
        assert logs[0]["status"] == "test_status"

def test_write_json_log_with_error(mock_logs_dir):
    """Test writing logs with error information."""
    write_json_log(
        platform="test_platform",
        status="error_test",
        error="Test error message"
    )
    
    log_file = mock_logs_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(log_file) as f:
        logs = json.load(f)
        assert logs[0]["error"] == "Test error message"

def test_log_rotation(mock_logs_dir):
    """Test log rotation functionality."""
    # Create a large log file
    log_file = mock_logs_dir / f"test_platform-{datetime.now().strftime('%Y-%m-%d')}.json"
    large_log = ["x" * 1024] * (MAX_LOG_SIZE // 1024 + 1)  # Create a file larger than MAX_LOG_SIZE

    with open(log_file, 'w') as f:
        json.dump(large_log, f)

    # Write a new log entry to trigger rotation
    write_json_log(
        platform="test_platform",
        status="rotation_test"
    )

    # Check if rotation occurred
    assert log_file.exists()
    with open(log_file) as f:
        logs = json.load(f)
        assert len(logs) == 1  # Should only contain the new log entry

    # Check if rotated file was compressed
    rotated_files = list(mock_logs_dir.glob("*.gz"))
    assert len(rotated_files) == 1

def test_log_compression(mock_logs_dir):
    """Test log compression for old files."""
    # Create an old log file
    old_date = datetime.now() - timedelta(days=COMPRESS_AFTER + 1)
    old_log_file = mock_logs_dir / f"test_platform-{old_date.strftime('%Y-%m-%d')}.json"

    with open(old_log_file, 'w') as f:
        json.dump({"test": "data"}, f)

    # Set the file's modification time to match the old date
    old_timestamp = old_date.timestamp()
    os.utime(old_log_file, (old_timestamp, old_timestamp))

    # Trigger rotation
    rotate_logs()

    # Check if file was compressed
    compressed_file = old_log_file.with_suffix('.json.gz')
    assert compressed_file.exists()

def test_read_logs(mock_logs_dir):
    """Test reading logs with filters."""
    # Write test logs
    write_json_log(
        platform="test_platform",
        status="success",
        tags=["test"]
    )
    
    write_json_log(
        platform="test_platform",
        status="failure",
        tags=["error"]
    )
    
    # Test reading all logs
    logs = read_logs("test_platform")
    assert len(logs) == 2
    
    # Test filtering by status
    success_logs = read_logs("test_platform", status="success")
    assert len(success_logs) == 1
    assert success_logs[0]["status"] == "success"
    
    # Test filtering by tags
    error_logs = read_logs("test_platform", tags=["error"])
    assert len(error_logs) == 1
    assert "error" in error_logs[0]["tags"]

def test_read_logs_with_compressed_files(mock_logs_dir):
    """Test reading logs from compressed files."""
    # Create and compress an old log file
    old_date = datetime.now() - timedelta(days=COMPRESS_AFTER + 1)
    old_log_file = mock_logs_dir / f"test_platform-{old_date.strftime('%Y-%m-%d')}.json"

    test_data = [{
        "timestamp": old_date.isoformat(),
        "platform": "test_platform",
        "status": "success",
        "tags": ["compressed"],
        "metadata": {"test": "compressed_data"}
    }]

    with open(old_log_file, 'w') as f:
        json.dump(test_data, f)

    # Set the file's modification time to match the old date
    old_timestamp = old_date.timestamp()
    os.utime(old_log_file, (old_timestamp, old_timestamp))

    # Compress the file
    with open(old_log_file, 'rb') as f_in:
        with gzip.open(f"{old_log_file}.gz", 'wb') as f_out:
            f_out.writelines(f_in)
    os.remove(old_log_file)

    # Test reading from compressed file
    logs = read_logs("test_platform")
    assert len(logs) == 1
    assert logs[0]["tags"] == ["compressed"]

def test_error_handling(mock_logs_dir):
    """Test error handling in log operations."""
    # Test writing to invalid directory
    invalid_path = "/root/doesnotexist/invalid-log.json"
    with pytest.raises(Exception):
        write_json_log(
            platform="test_platform",
            status="error_test",
            path_override=invalid_path
        ) 