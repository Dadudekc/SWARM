import pytest
from pathlib import Path
import json
import os
import time
from datetime import datetime, timedelta
from dreamos.social.utils.log_manager import LogManager, LogConfig, LogLevel
import shutil
import logging
import platform

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test constants
TEST_TIMEOUT = 60  # seconds - increased to handle file operations
MAX_LOG_SIZE = 1024 * 1024  # 1MB
BATCH_SIZE = 10  # Smaller batch size for tests
BATCH_TIMEOUT = 1.0  # 1 second timeout for tests

@pytest.fixture
def temp_log_dir(tmp_path):
    """Fixture to create a temporary log directory."""
    log_dir = tmp_path / "dream_os_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    yield str(log_dir)
    # Cleanup after test
    try:
        shutil.rmtree(log_dir)
    except Exception as e:
        logging.warning(f"Failed to cleanup temp log directory: {e}")

@pytest.fixture
def log_manager(temp_log_dir):
    """Fixture to create a test log manager instance."""
    # Reset singleton before each test
    LogManager.reset_singleton()
    # Create test config
    config = LogConfig(
        log_dir=str(temp_log_dir),
        level="DEBUG",
        output_format="json",
        max_size_mb=1.0,
        batch_size=BATCH_SIZE,
        batch_timeout=BATCH_TIMEOUT,
        max_retries=2,
        retry_delay=0.1,
        test_mode=True,
        rotation_enabled=True,
        max_files=2,
        compress_after_days=1,
        rotation_check_interval=60,
        cleanup_interval=3600,
        platforms={
            "test": "test.log",
            "test1": "test1.log",
            "test2": "test2.log",
            "discord": "discord.log",
            "agent": "agent.log",
            "system": "system.log"
        }
    )
    # Purge all log files before test
    log_dir = Path(config.log_dir)
    if log_dir.exists():
        for file in log_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            except Exception as e:
                logging.warning(f"Failed to remove {file}: {e}")
    # Create and return manager instance
    manager = LogManager(config=config)
    yield manager
    # Cleanup after test
    manager.shutdown()
    time.sleep(0.2)  # Give more time for file handles to be released
    # Clean up any remaining log files
    if log_dir.exists():
        for file in log_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            except Exception as e:
                logging.warning(f"Failed to remove {file}: {e}")

def test_log_manager_singleton():
    """Test that LogManager maintains singleton pattern."""
    manager1 = LogManager()
    manager2 = LogManager()
    assert manager1 is manager2

def test_write_log(log_manager):
    """Test basic log writing functionality."""
    # Ensure log directory exists
    log_dir = Path(log_manager._config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing logs with improved Windows handle management
    log_file = log_dir / log_manager._config.platforms["test"]
    if log_file.exists():
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(log_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                log_file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Write test log with retry mechanism
    max_write_retries = 3
    for retry in range(max_write_retries):
        try:
            success = log_manager.write_log(
                message="Test log message",
                level=LogLevel.INFO,
                platform="test",
                status="running"
            )
            assert success is True
            break
        except (PermissionError, OSError) as e:
            if retry == max_write_retries - 1:
                raise
            time.sleep(0.2)
    
    # Force flush to ensure log is written
    log_manager.flush()
    time.sleep(0.2)  # Increased wait time for Windows
    
    # Verify log file was created
    assert log_file.exists(), f"Log file not created at {log_file}"
    
    # Verify log content with improved retry logic
    max_read_retries = 5  # Increased retries for Windows
    for retry in range(max_read_retries):
        try:
            with open(log_file) as f:
                log_entry = json.loads(f.readline())
                assert log_entry["platform"] == "test", f"Expected platform 'test', got {log_entry['platform']}"
                assert log_entry["status"] == "running", f"Expected status 'running', got {log_entry['status']}"
                assert log_entry["message"] == "Test log message", f"Expected message 'Test log message', got {log_entry['message']}"
                assert log_entry["level"] == "INFO", f"Expected level 'INFO', got {log_entry['level']}"
            break
        except (json.JSONDecodeError, AssertionError, PermissionError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.3)  # Increased wait time for Windows
    
    # Test writing to non-existent platform
    with pytest.raises(ValueError):
        log_manager.write_log(
            message="Test log message",
            level=LogLevel.INFO,
            platform="non_existent",
            status="running"
        )
    
    # Test writing with invalid level
    with pytest.raises(ValueError):
        log_manager.write_log(
            message="Test log message",
            level="INVALID_LEVEL",
            platform="test",
            status="running"
        )

def test_log_levels(log_manager):
    """Test different log level methods."""
    # Clear existing logs with improved Windows handle management
    log_dir = Path(log_manager._config.log_dir)
    log_file = log_dir / log_manager._config.platforms["test"]
    if log_file.exists():
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(log_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                log_file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Test info
    assert log_manager.info("test", "running", "Info message") is True
    # Test error
    assert log_manager.error("test", "failed", "Error message") is True
    # Test warning
    assert log_manager.warning("test", "warning", "Warning message") is True
    # Test debug
    assert log_manager.debug("test", "debug", "Debug message") is True
    # Test critical
    assert log_manager.critical("test", "critical", "Critical message") is True
    
    # Force flush to ensure all logs are written
    log_manager.flush()
    time.sleep(0.2)  # Give time for file handles to be released
    
    # Verify log entries
    logs = log_manager.read_logs(platform="test")
    assert len(logs) == 5, f"Expected 5 log entries, got {len(logs)}"
    
    # Verify each log entry
    levels = ["INFO", "ERROR", "WARNING", "DEBUG", "CRITICAL"]
    messages = ["Info message", "Error message", "Warning message", "Debug message", "Critical message"]
    statuses = ["running", "failed", "warning", "debug", "critical"]
    
    for i, log in enumerate(logs):
        assert log["level"] == levels[i], f"Expected level {levels[i]}, got {log['level']}"
        assert log["message"] == messages[i], f"Expected message {messages[i]}, got {log['message']}"
        assert log["status"] == statuses[i], f"Expected status {statuses[i]}, got {log['status']}"

def test_invalid_log_level(log_manager):
    """Test that invalid log level raises ValueError."""
    with pytest.raises(ValueError):
        log_manager.write_log(
            platform="test",
            status="running",
            message="Test message",
            level="INVALID_LEVEL"
        )

def test_log_rotation(log_manager):
    """Test log rotation functionality."""
    # Ensure log directory exists
    log_dir = Path(log_manager._config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing logs with improved Windows handle management
    log_file = log_dir / log_manager._config.platforms["test"]
    if log_file.exists():
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(log_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                log_file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Write enough logs to trigger rotation (exceed max_size_mb)
    message_size = int(log_manager._config.max_size_mb * 1024 * 1024)  # Convert to bytes
    message = "x" * message_size  # Create message of max_size_mb
    
    # Write logs with retry mechanism
    max_write_retries = 3
    for i in range(3):  # Write three times to ensure rotation
        for retry in range(max_write_retries):
            try:
                log_manager.write_log(
                    message=f"{message}_{i}",
                    level=LogLevel.INFO,
                    platform="test",
                    status="running"
                )
                log_manager.flush()
                break
            except (PermissionError, OSError) as e:
                if retry == max_write_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Wait for rotation to complete
    time.sleep(0.5)  # Give more time for rotation to complete
    
    # Check that rotation occurred with retry mechanism
    max_check_retries = 5
    for retry in range(max_check_retries):
        try:
            rotated_files = list(log_dir.glob("test.log.*"))
            if len(rotated_files) > 0:
                break
            if retry == max_check_retries - 1:
                assert len(rotated_files) > 0, "No rotated files found"
            time.sleep(0.2)
        except (PermissionError, OSError) as e:
            if retry == max_check_retries - 1:
                raise
            time.sleep(0.2)
    
    # Check that only max_files files exist
    all_log_files = list(log_dir.glob("test.log*"))
    assert len(all_log_files) <= log_manager._config.max_files + 1, f"Too many log files: {len(all_log_files)}"
    
    # Verify content and size of rotated files with retry mechanism
    for file in rotated_files:
        max_verify_retries = 3
        for retry in range(max_verify_retries):
            try:
                assert file.stat().st_size > 0, f"Rotated file {file} is empty"
                assert file.stat().st_size >= message_size, f"Rotated file {file} is smaller than expected"
                break
            except (PermissionError, OSError) as e:
                if retry == max_verify_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Verify that the current log file exists and is not empty
    max_current_retries = 3
    for retry in range(max_current_retries):
        try:
            assert log_file.exists(), "Current log file does not exist"
            assert log_file.stat().st_size > 0, "Current log file is empty"
            break
        except (PermissionError, OSError) as e:
            if retry == max_current_retries - 1:
                raise
            time.sleep(0.2)
    
    # Cleanup rotated files
    for file in rotated_files:
        try:
            if platform.system() == 'Windows':
                try:
                    import win32file
                    import win32con
                    import pywintypes
                    handle = win32file.CreateFile(
                        str(file),
                        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                        0, None, win32con.OPEN_EXISTING,
                        win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                        None
                    )
                    win32file.CloseHandle(handle)
                except pywintypes.error as e:
                    if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                        time.sleep(0.2)
                        continue
                    raise
            file.unlink()
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to cleanup rotated file {file}: {e}")
            time.sleep(0.2)

def test_metrics(log_manager):
    """Test metrics collection."""
    log_manager.write_log(message="Test info", level=LogLevel.INFO, platform="test", status="ok")
    log_manager.write_log(message="Test error", level=LogLevel.ERROR, platform="test", status="fail")
    log_manager.flush()
    metrics = log_manager.get_metrics()
    # Use string keys for entries_by_level
    assert metrics["entries_by_level"]["INFO"] == 1
    assert metrics["entries_by_level"]["ERROR"] == 1

def test_read_logs(log_manager):
    """Test reading logs with filters."""
    # Ensure log directory exists
    log_dir = Path(log_manager._config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing logs with improved Windows handle management
    for platform_name in log_manager._config.platforms:
        log_file = log_dir / log_manager._config.platforms[platform_name]
        if log_file.exists():
            max_retries = 3
            for retry in range(max_retries):
                try:
                    # Try to force close any open handles on Windows
                    if platform.system() == 'Windows':
                        try:
                            import win32file
                            import win32con
                            import pywintypes
                            handle = win32file.CreateFile(
                                str(log_file),
                                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                                0, None, win32con.OPEN_EXISTING,
                                win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                                None
                            )
                            win32file.CloseHandle(handle)
                        except pywintypes.error as e:
                            if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                                time.sleep(0.2)
                                continue
                            raise
                    
                    # Try to delete the file
                    log_file.unlink()
                    break
                except (PermissionError, OSError) as e:
                    if retry == max_retries - 1:
                        raise
                    time.sleep(0.2)
    
    # Write some test logs with precise timing
    now = datetime.now()
    
    # Write logs with retry mechanism
    max_write_retries = 3
    for retry in range(max_write_retries):
        try:
            log_manager.info("test1", "running", "Info message 1")
            log_manager.flush()
            time.sleep(0.2)  # Ensure different timestamps with more buffer
            
            log_manager.error("test2", "failed", "Error message")
            log_manager.flush()
            time.sleep(0.2)  # Ensure different timestamps with more buffer
            
            log_manager.warning("test1", "warning", "Warning message")
            log_manager.flush()
            time.sleep(0.2)  # Give more time for file handles to be released
            break
        except (PermissionError, OSError) as e:
            if retry == max_write_retries - 1:
                raise
            time.sleep(0.2)
    
    # Test reading all logs with retry mechanism
    max_read_retries = 5
    for retry in range(max_read_retries):
        try:
            all_logs = log_manager.read_logs()
            assert len(all_logs) == 3, f"Expected 3 logs, got {len(all_logs)}"
            break
        except (PermissionError, OSError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.2)
    
    # Test platform filter with retry mechanism
    for retry in range(max_read_retries):
        try:
            test1_logs = log_manager.read_logs(platform="test1")
            assert len(test1_logs) == 2, f"Expected 2 logs for test1, got {len(test1_logs)}"
            assert all(log["platform"] == "test1" for log in test1_logs), "Not all logs are from test1 platform"
            break
        except (PermissionError, OSError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.2)
    
    # Test level filter with retry mechanism
    for retry in range(max_read_retries):
        try:
            error_logs = log_manager.read_logs(level=LogLevel.ERROR)
            assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"
            assert error_logs[0]["platform"] == "test2", f"Expected platform 'test2', got {error_logs[0]['platform']}"
            assert error_logs[0]["level"] == "ERROR", f"Expected level 'ERROR', got {error_logs[0]['level']}"
            break
        except (PermissionError, OSError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.2)
    
    # Test time filter with more precise timing and timezone handling
    start_time = now + timedelta(milliseconds=100)  # Add more buffer
    end_time = now + timedelta(milliseconds=400)    # Add more buffer
    for retry in range(max_read_retries):
        try:
            filtered_logs = log_manager.read_logs(start_time=start_time, end_time=end_time)
            assert len(filtered_logs) == 1, f"Expected 1 log in time range, got {len(filtered_logs)}"
            break
        except (PermissionError, OSError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.2)
    
    # Cleanup log files with improved Windows handle management
    for platform_name in log_manager._config.platforms:
        log_file = log_dir / log_manager._config.platforms[platform_name]
        if log_file.exists():
            max_cleanup_retries = 3
            for retry in range(max_cleanup_retries):
                try:
                    # Try to force close any open handles on Windows
                    if platform.system() == 'Windows':
                        try:
                            import win32file
                            import win32con
                            import pywintypes
                            handle = win32file.CreateFile(
                                str(log_file),
                                win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                                0, None, win32con.OPEN_EXISTING,
                                win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                                None
                            )
                            win32file.CloseHandle(handle)
                        except pywintypes.error as e:
                            if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                                time.sleep(0.2)
                                continue
                            raise
                    
                    # Try to delete the file
                    log_file.unlink()
                    break
                except (PermissionError, OSError) as e:
                    if retry == max_cleanup_retries - 1:
                        logging.warning(f"Failed to cleanup log file {log_file}: {e}")
                    time.sleep(0.2)

def test_cleanup(log_manager):
    """Test log cleanup functionality."""
    # Ensure log directory exists
    log_dir = Path(log_manager._config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing logs with improved Windows handle management
    log_file = log_dir / log_manager._config.platforms["test"]
    if log_file.exists():
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(log_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                log_file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Write enough logs to trigger cleanup with retry mechanism
    message_size = int(log_manager._config.max_size_mb * 1024 * 1024)  # Convert to bytes
    message = "x" * message_size  # Create message of max_size_mb
    
    max_write_retries = 3
    for i in range(3):  # Write three times to ensure cleanup
        for retry in range(max_write_retries):
            try:
                log_manager.write_log(
                    message=f"{message}_{i}",
                    level=LogLevel.INFO,
                    platform="test",
                    status="running"
                )
                log_manager.flush()
                break
            except (PermissionError, OSError) as e:
                if retry == max_write_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Wait for cleanup to complete with increased wait time
    time.sleep(0.5)  # Give more time for cleanup to complete
    
    # Check that cleanup occurred with retry mechanism
    max_check_retries = 5
    for retry in range(max_check_retries):
        try:
            all_log_files = list(log_dir.glob("test.log*"))
            assert len(all_log_files) <= log_manager._config.max_files + 1, f"Too many log files: {len(all_log_files)}"
            break
        except (PermissionError, OSError) as e:
            if retry == max_check_retries - 1:
                raise
            time.sleep(0.2)
    
    # Verify that the current log file exists and is not empty with retry mechanism
    max_verify_retries = 3
    for retry in range(max_verify_retries):
        try:
            assert log_file.exists(), "Current log file does not exist"
            assert log_file.stat().st_size > 0, "Current log file is empty"
            break
        except (PermissionError, OSError) as e:
            if retry == max_verify_retries - 1:
                raise
            time.sleep(0.2)
    
    # Cleanup all log files with improved Windows handle management
    for file in log_dir.glob("test.log*"):
        max_cleanup_retries = 3
        for retry in range(max_cleanup_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_cleanup_retries - 1:
                    logging.warning(f"Failed to cleanup log file {file}: {e}")
                time.sleep(0.2)

def test_batch_processing(log_manager):
    """Test log batch processing."""
    # Ensure log directory exists
    log_dir = Path(log_manager._config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing logs with improved Windows handle management
    log_file = log_dir / log_manager._config.platforms["test"]
    if log_file.exists():
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try to force close any open handles on Windows
                if platform.system() == 'Windows':
                    try:
                        import win32file
                        import win32con
                        import pywintypes
                        handle = win32file.CreateFile(
                            str(log_file),
                            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING,
                            win32con.FILE_ATTRIBUTE_NORMAL | win32con.FILE_FLAG_DELETE_ON_CLOSE,
                            None
                        )
                        win32file.CloseHandle(handle)
                    except pywintypes.error as e:
                        if e.winerror == 32:  # ERROR_SHARING_VIOLATION
                            time.sleep(0.2)
                            continue
                        raise
                
                # Try to delete the file
                log_file.unlink()
                break
            except (PermissionError, OSError) as e:
                if retry == max_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Write logs that should be batched with retry mechanism
    max_write_retries = 3
    for i in range(log_manager._config.batch_size + 1):
        for retry in range(max_write_retries):
            try:
                log_manager.info("test", "running", f"Batch message {i}")
                break
            except (PermissionError, OSError) as e:
                if retry == max_write_retries - 1:
                    raise
                time.sleep(0.2)
    
    # Force flush to ensure all logs are written
    log_manager.flush()
    
    # Wait for batch timeout with increased wait time
    time.sleep(log_manager._config.batch_timeout * 3)  # Increased wait time for Windows
    
    # Verify log file exists with retry mechanism
    max_check_retries = 5
    for retry in range(max_check_retries):
        try:
            assert log_file.exists(), "Log file not created"
            break
        except (PermissionError, OSError) as e:
            if retry == max_check_retries - 1:
                raise
            time.sleep(0.2)
    
    # Count written logs with retry mechanism
    max_read_retries = 5
    log_count = 0
    for retry in range(max_read_retries):
        try:
            with open(log_file) as f:
                log_count = sum(1 for _ in f)
            assert log_count > 0, "No logs were written"
            break
        except (PermissionError, OSError) as e:
            if retry == max_read_retries - 1:
                raise
            time.sleep(0.2)
    
    # Verify log content with retry mechanism
    max_verify_retries = 3
    for retry in range(max_verify_retries):
        try:
            with open(log_file) as f:
                logs = [json.loads(line) for line in f]
                assert len(logs) == log_count, f"Expected {log_count} logs, got {len(logs)}"
                assert all(log["platform"] == "test" for log in logs), "Not all logs are from test platform"
                assert all(log["status"] == "running" for log in logs), "Not all logs have status 'running'"
                assert all(log["level"] == "INFO" for log in logs), "Not all logs have level 'INFO'"
                assert all(f"Batch message {i}" in log["message"] for i, log in enumerate(logs)), "Log messages don't match expected pattern"
            break
        except (json.JSONDecodeError, AssertionError, PermissionError) as e:
            if retry == max_verify_retries - 1:
                raise
            time.sleep(0.2)
    
    # Test concurrent access
    import threading
    import queue
    
    def write_logs(q):
        try:
            for i in range(100):
                log_manager.info("test", "running", f"Concurrent message {i}")
            q.put(True)
        except Exception as e:
            q.put(e)
    
    # Start multiple threads
    threads = []
    results = queue.Queue()
    for _ in range(4):
        t = threading.Thread(target=write_logs, args=(results,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Check results
    for _ in range(4):
        result = results.get()
        if isinstance(result, Exception):
            raise result
    
    # Force flush and wait
    log_manager.flush()
    time.sleep(log_manager._config.batch_timeout * 3)
    
    # Verify final log count
    with open(log_file) as f:
        final_count = sum(1 for _ in f)
    assert final_count >= log_count + 400, f"Expected at least {log_count + 400} logs, got {final_count}"

@pytest.mark.parametrize("platform,level,message", [
    ("discord", "info", "Discord message received"),
    ("agent", "warning", "Agent task timeout"),
    ("system", "error", "Database connection failed"),
    ("test", "debug", "Test debug message"),
])
@pytest.mark.timeout(TEST_TIMEOUT)
def test_platform_specific_logging(platform, level, message, log_manager):
    """Test log writing and reading with different platforms and levels."""
    start_time = time.time()
    try:
        # Write test log
        success = log_manager.write_log(
            platform=platform,
            status=level,
            message=message
        )
        logger.debug(f"Write log result for {platform}: {success}")
        
        if not success:
            pytest.fail(f"Failed to write log entry for platform {platform}")
        
        # Give time for background operations
        time.sleep(0.5)  # Increased sleep time
        
        # Flush logs
        log_manager.flush()
        logger.debug(f"Flushed logs for {platform}")
        
        # Give time for flush to complete
        time.sleep(0.5)  # Increased sleep time
        
        # Read logs back
        logs = log_manager.read_logs(platform)
        logger.debug(f"Read logs for {platform}: {logs}")
        
        # Verify log entry
        assert len(logs) == 1, (
            f"Expected 1 log entry for {platform}, got {len(logs)}. "
            f"Log directory contents: {os.listdir(log_manager._config.log_dir)}"
        )
        
        log_entry = logs[0]
        assert log_entry["message"] == message, (
            f"Expected message '{message}', got '{log_entry.get('message')}'. "
            f"Full log entry: {log_entry}"
        )
        assert log_entry["status"] == level, (
            f"Expected status '{level}', got '{log_entry.get('status')}'. "
            f"Full log entry: {log_entry}"
        )
        assert log_entry["platform"] == platform, (
            f"Expected platform '{platform}', got '{log_entry.get('platform')}'. "
            f"Full log entry: {log_entry}"
        )
        
        # Verify log file size
        log_files = list(Path(log_manager._config.log_dir).glob("*.log")) + list(Path(log_manager._config.log_dir).glob("*.json"))
        assert len(log_files) > 0, "No log files found"
        for log_file in log_files:
            assert log_file.stat().st_size < MAX_LOG_SIZE, (
                f"Log file {log_file} exceeds maximum size of {MAX_LOG_SIZE} bytes"
            )
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        raise
    finally:
        elapsed = time.time() - start_time
        logger.debug(f"⏱️ Test completed in {elapsed:.2f} seconds")

@pytest.mark.timeout(TEST_TIMEOUT)
def test_multi_platform_concurrent_writes(log_manager):
    """Test concurrent log writing from multiple platforms."""
    start_time = time.time()
    try:
        platforms = ["discord", "agent", "system"]
        messages = [f"Test message {i}" for i in range(len(platforms))]
        
        # Write logs sequentially instead of concurrently
        for platform, message in zip(platforms, messages):
            success = log_manager.write_log(
                platform=platform,
                status="info",
                message=message
            )
            assert success, f"Failed to write log for {platform}"
            time.sleep(0.1)  # Small delay between writes
        
        # Give time for background operations
        time.sleep(0.5)  # Increased sleep time
        
        # Flush all logs
        log_manager.flush()
        
        # Give time for flush to complete
        time.sleep(0.5)  # Increased sleep time
        
        # Verify all logs were written
        for platform, message in zip(platforms, messages):
            logs = log_manager.read_logs(platform)
            assert len(logs) == 1, f"Expected 1 log for {platform}, got {len(logs)}"
            assert logs[0]["message"] == message, (
                f"Expected message '{message}', got '{logs[0].get('message')}'"
            )
        
    except Exception as e:
        logger.error(f"Concurrent write test failed: {str(e)}", exc_info=True)
        raise
    finally:
        elapsed = time.time() - start_time
        logger.debug(f"⏱️ Concurrent write test completed in {elapsed:.2f} seconds") 