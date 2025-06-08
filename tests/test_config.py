"""
Test configuration and environment setup.
"""

import os
import pytest
import shutil
import json
from pathlib import Path
import logging
from typing import Generator, Dict, Any
from tests.utils.test_utils import (
    safe_remove, TEST_ROOT, TEST_DATA_DIR, TEST_OUTPUT_DIR,
    VOICE_QUEUE_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR,
    ensure_test_dirs
)
import yaml
from dreamos.core.config.config_manager import ConfigManager
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir,
    safe_rmdir
)

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

# Initialize logging
ensure_dir(Path("logs/tests/config"))
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/tests/config/test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_test_environment() -> Dict[str, Any]:
    """Set up test environment.
    
    Returns:
        Dict containing test environment configuration
    """
    try:
        # Create test directories
        test_dirs = {
            "data": Path("tests/data"),
            "output": Path("tests/output"),
            "config": Path("tests/config"),
            "runtime": Path("tests/runtime"),
            "temp": Path("tests/temp"),
            "logs": Path("logs/tests")
        }
        
        for dir_path in test_dirs.values():
            ensure_dir(dir_path)
            
        # Load test configuration with proper error handling
        try:
            config = read_json("config/test_config.json")
        except FileNotFoundError:
            config = {}
        
        # Add directory paths to config
        config["dirs"] = {k: str(v) for k, v in test_dirs.items()}
        
        return config
        
    except Exception as e:
        logger.error(f"Error setting up test environment: {str(e)}")
        return {}

def cleanup_test_environment() -> None:
    """Clean up test environment."""
    try:
        test_dirs = [
            Path("tests/output"),
            Path("tests/runtime"),
            Path("tests/temp")
        ]
        
        for dir_path in test_dirs:
            if dir_path.exists():
                safe_rmdir(dir_path, recursive=True)
                
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {str(e)}")

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

def test_log_level(tmp_path):
    """Test log level configuration and entry counting."""
    
    # Create a temporary log file
    log_file = tmp_path / "test.log"
    
    # Create a dedicated logger for this test
    logger = logging.getLogger("test_log_level")
    logger.setLevel(logging.INFO)  # Set to INFO level
    
    # Create a file handler
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Remove any existing handlers and add our file handler
    logger.handlers = []
    logger.addHandler(file_handler)
    
    # Write test log entries
    test_messages = [
        "Debug message",
        "Info message",
        "Warning message",
        "Error message"
    ]
    
    logger.debug(test_messages[0])
    logger.info(test_messages[1])
    logger.warning(test_messages[2])
    logger.error(test_messages[3])
    
    # Remove handler and close file
    logger.removeHandler(file_handler)
    file_handler.close()
    
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

def test_json_config_access(tmp_path):
    """Test JSON configuration access and dot notation."""
    data = {
        "logging": {
            "log_dir": str(tmp_path / "logs"),
            "level": "INFO"
        },
        "backend": {
            "url": "http://localhost"
        }
    }
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    config = ConfigManager(cfg_path)

    assert config.get("logging.log_dir") == str(tmp_path / "logs")
    assert config.get("backend.url") == "http://localhost"
    assert config.get("logging.level") == "INFO"

def test_json_config_integration_with_log_manager(tmp_path):
    """Test JSON configuration integration with log manager."""
    log_dir = tmp_path / "logs"
    cfg_path = tmp_path / "config.json"
    data = {
        "logging": {
            "log_dir": str(log_dir),
            "platforms": {
                "system": "system.log"
            }
        }
    }
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    config = ConfigManager(cfg_path)
    log_dir = Path(config.get("logging.log_dir"))
    platforms = config.get("logging.platforms")
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Write test log entry
    log_file = log_dir / platforms["system"]
    with open(log_file, "w") as f:
        f.write("test log entry")
    
    assert log_file.exists(), "Log file should exist"
    with open(log_file) as f:
        content = f.read()
        assert "test log entry" in content

def test_bridge_specific_config(tmp_path):
    """Test bridge-specific configuration handling."""
    data = {
        "bridge": {
            "inbox": str(tmp_path / "inbox"),
            "outbox": str(tmp_path / "outbox"),
            "max_retries": 3,
            "retry_delay": 5
        }
    }
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    config = ConfigManager(cfg_path)
    bridge_config = config.get_bridge_config()

    assert bridge_config["inbox"] == str(tmp_path / "inbox")
    assert bridge_config["outbox"] == str(tmp_path / "outbox")
    assert bridge_config["max_retries"] == 3
    assert bridge_config["retry_delay"] == 5

def test_config_validation(tmp_path):
    """Test configuration validation."""
    data = {
        "logging": {
            "log_dir": str(tmp_path / "logs"),
            "level": "INVALID_LEVEL"  # Invalid log level
        }
    }
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    config = ConfigManager(cfg_path)
    
    # Invalid log level should be replaced with default
    assert config.get("logging.level") == "INFO"

def test_file_permissions(tmp_path):
    """Test file permissions handling."""
    data = {
        "logging": {
            "log_dir": str(tmp_path / "logs"),
            "level": "INFO"
        }
    }
    cfg_path = tmp_path / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f)

    config = ConfigManager(cfg_path)
    log_dir = Path(config.get("logging.log_dir"))
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Test file permissions
    if os.name != 'nt':  # Skip on Windows
        assert oct(log_dir.stat().st_mode)[-3:] == '700', "Log directory should have 700 permissions"
        assert oct(cfg_path.stat().st_mode)[-3:] == '600', "Config file should have 600 permissions"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    config = setup_test_environment()
    yield
    cleanup_test_environment()

@pytest.fixture(scope="session", autouse=True)
def test_env() -> Generator[Dict[str, Any], None, None]:
    """Test environment fixture."""
    config = setup_test_environment()
    yield config
    cleanup_test_environment()

@pytest.fixture(scope="function")
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    try:
        return read_json("config/test_config.json", default={})
    except Exception as e:
        logger.error(f"Error loading test config: {str(e)}")
        return {
            "log_level": "DEBUG",
            "max_retries": 3,
            "timeout": 5,
            "rate_limit": {
                "requests": 10,
                "period": 60
            }
        }

@pytest.fixture(scope="function")
def test_data_dir() -> Path:
    """Test data directory fixture."""
    data_dir = Path("tests/data")
    ensure_dir(data_dir)
    return data_dir

@pytest.fixture(scope="function")
def test_output_dir() -> Path:
    """Test output directory fixture."""
    output_dir = Path("tests/output")
    ensure_dir(output_dir)
    return output_dir

@pytest.fixture(scope="function")
def test_runtime_dir() -> Path:
    """Test runtime directory fixture."""
    runtime_dir = Path("tests/runtime")
    ensure_dir(runtime_dir)
    return runtime_dir

@pytest.fixture(scope="function")
def test_temp_dir() -> Path:
    """Test temporary directory fixture."""
    temp_dir = Path("tests/temp")
    ensure_dir(temp_dir)
    return temp_dir 
