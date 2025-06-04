"""
Test configuration and environment setup.
"""

import os
import pytest
import shutil
from pathlib import Path
import logging
from typing import Generator
from tests.utils.test_utils import (
    safe_remove, TEST_ROOT, TEST_DATA_DIR, TEST_OUTPUT_DIR,
    VOICE_QUEUE_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR,
    ensure_test_dirs
)
import yaml

# Test constants - Use relative paths from TEST_ROOT
MOCK_AGENT_CONFIG = {
    "username": "test_user",
    "password": "test_pass",
    "log_dir": "logs",  # Relative path that will be resolved in tests
    "max_size": 1024,
    "max_age": 7,
    "batch_size": 100,
    "batch_timeout": 5,
    "rotation_check_interval": 60,
    "compress_after": 3
}
MOCK_PROMPT = "Test prompt content"
MOCK_DEVLOG = "Test devlog content"

def setup_test_environment() -> None:
    """Set up the test environment."""
    ensure_test_dirs()
    # Create log directory structure
    log_dir = TEST_RUNTIME_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

def cleanup_test_environment() -> None:
    """Clean up the test environment."""
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, 
                     TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if directory.exists():
            safe_remove(directory)

def test_config_defaults():
    """Test default configuration values."""
    
    # Create config with absolute path
    config = {
        "agent_id": "test_agent",
        "platform": "test",
        "credentials": {
            "username": "test_user",
            "password": "test_pass"
        },
        "log_dir": str(TEST_RUNTIME_DIR / "logs")  # Use absolute path
    }
    
    # Save config
    config_path = TEST_CONFIG_DIR / "agent_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    # Verify config
    assert config_path.exists(), "Config file should exist"
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)
        assert loaded_config["agent_id"] == "test_agent"
        assert loaded_config["log_dir"] == str(TEST_RUNTIME_DIR / "logs")
        
        # Create and verify log directory
        log_dir = Path(loaded_config["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        assert log_dir.exists(), "Log directory should exist"
        assert os.access(log_dir, os.W_OK), "Log directory should be writable"
        
        # Test writing to log directory
        test_log_file = log_dir / "test.log"
        with open(test_log_file, "w") as f:
            f.write("test log entry")
        assert test_log_file.exists(), "Should be able to write to log directory"

def test_config_custom_values():
    """Test custom configuration values."""
    
    # Create config with custom values using absolute path
    custom_log_dir = str(TEST_RUNTIME_DIR / "custom_logs")
    config = {
        "agent_id": "test_agent",
        "platform": "test",
        "credentials": {
            "username": "custom_user",
            "password": "custom_pass"
        },
        "log_dir": custom_log_dir
    }
    
    # Save config
    config_path = TEST_CONFIG_DIR / "agent_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    # Verify config
    assert config_path.exists(), "Config file should exist"
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)
        assert loaded_config["agent_id"] == "test_agent"
        assert loaded_config["log_dir"] == custom_log_dir
        
        # Create and verify custom log directory
        log_dir = Path(loaded_config["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        assert log_dir.exists(), "Custom log directory should exist"
        assert os.access(log_dir, os.W_OK), "Custom log directory should be writable"
        
        # Test writing to custom log directory
        test_log_file = log_dir / "test.log"
        with open(test_log_file, "w") as f:
            f.write("test log entry")
        assert test_log_file.exists(), "Should be able to write to custom log directory"

def test_invalid_log_dir():
    """Test handling of invalid log directory."""
    
    # Try to create config with invalid log directory
    invalid_log_dir = str(TEST_RUNTIME_DIR / "invalid" / "log" / "dir")
    config = {
        "agent_id": "test_agent",
        "platform": "test",
        "credentials": {
            "username": "test_user",
            "password": "test_pass"
        },
        "log_dir": invalid_log_dir
    }
    
    # Save config
    config_path = TEST_CONFIG_DIR / "agent_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    # Verify config
    assert config_path.exists(), "Config file should exist"
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)
        assert loaded_config["agent_id"] == "test_agent"
        assert loaded_config["log_dir"] == invalid_log_dir
        
        # Verify invalid log directory is not created
        log_dir = Path(loaded_config["log_dir"])
        assert not log_dir.exists(), "Invalid log directory should not exist"

        # Create a file where the log directory should be to simulate an invalid path
        invalid_parent = log_dir.parent.parent
        if invalid_parent.exists():
            safe_remove(invalid_parent)
        invalid_parent.touch()

        # Test that attempting to create the directory fails
        with pytest.raises((OSError, PermissionError)):
            log_dir.mkdir(parents=True, exist_ok=True)

def test_log_level():
    """Test log level configuration and entry counting."""
    
    # Create config with log level
    config = {
        "agent_id": "test_agent",
        "platform": "test",
        "credentials": {
            "username": "test_user",
            "password": "test_pass"
        },
        "log_dir": "logs",
        "log_level": "INFO"
    }
    
    # Save config
    config_path = TEST_CONFIG_DIR / "agent_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    # Create log directory
    log_dir = TEST_RUNTIME_DIR / config["log_dir"]
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    log_file = log_dir / "test.log"
    # Ensure any previous log data is removed so tests run in isolation
    log_file.unlink(missing_ok=True)
    logging.basicConfig(
        level=config["log_level"],
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=str(log_file),
        force=True
    )
    
    # Write test log entries
    test_messages = [
        "Debug message",
        "Info message",
        "Warning message",
        "Error message"
    ]
    
    logging.debug(test_messages[0])
    logging.info(test_messages[1])
    logging.warning(test_messages[2])
    logging.error(test_messages[3])

    logging.shutdown()
    
    # Verify log file exists and contains entries
    assert log_file.exists(), "Log file should exist"
    
    # Count log entries
    with open(log_file) as f:
        log_content = f.read()
        entry_count = len(log_content.strip().splitlines())
        assert entry_count == 3, f"Should have 3 log entries (INFO and above), got {entry_count}"
        
        # Verify specific messages are present/absent based on log level
        assert test_messages[0] not in log_content, "Debug message should not be logged"
        assert test_messages[1] in log_content, "Info message should be logged"
        assert test_messages[2] in log_content, "Warning message should be logged"
        assert test_messages[3] in log_content, "Error message should be logged"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    setup_test_environment()
    yield
    cleanup_test_environment() 
