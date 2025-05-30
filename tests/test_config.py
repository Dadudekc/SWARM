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

# Test constants
MOCK_AGENT_CONFIG = {
    "username": "test_user",
    "password": "test_pass",
    "log_dir": str(TEST_RUNTIME_DIR / "logs"),  # Use test runtime directory
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

def cleanup_test_environment() -> None:
    """Clean up the test environment."""
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, 
                     TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if directory.exists():
            safe_remove(directory)

def test_cleanup():
    """Test that cleanup removes test directories."""
    cleanup_test_environment()
    assert not TEST_DATA_DIR.exists(), "test_data should be removed"
    assert not TEST_CONFIG_DIR.exists(), "test_config should be removed"
    assert not VOICE_QUEUE_DIR.exists(), "test_voice_queue should be removed"
    assert not TEST_OUTPUT_DIR.exists(), "test_output should be removed"
    assert not TEST_RUNTIME_DIR.exists(), "test_runtime should be removed"
    assert not TEST_TEMP_DIR.exists(), "test_temp should be removed"

def test_config_file_creation():
    """Test that config files are created."""
    config_path = TEST_CONFIG_DIR / "agent_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create default config
    config = {
        "agent_id": "test_agent",
        "platform": "test",
        "credentials": {
            "username": "test_user",
            "password": "test_pass"
        }
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    assert config_path.exists(), "Config file should exist"
    with open(config_path) as f:
        loaded_config = yaml.safe_load(f)
        assert loaded_config["agent_id"] == "test_agent"

def test_test_directories_creation():
    """Test that test directories are created."""
    # Create required directories
    (TEST_RUNTIME_DIR / "logs" / "screenshots").mkdir(parents=True, exist_ok=True)
    (TEST_RUNTIME_DIR / "logs" / "operations").mkdir(parents=True, exist_ok=True)
    (TEST_RUNTIME_DIR / "mailbox").mkdir(parents=True, exist_ok=True)
    
    assert (TEST_RUNTIME_DIR / "logs" / "screenshots").exists(), "screenshots directory should exist"
    assert (TEST_RUNTIME_DIR / "logs" / "operations").exists(), "operations directory should exist"
    assert (TEST_RUNTIME_DIR / "mailbox").exists(), "mailbox directory should exist"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    setup_test_environment()
    yield
    cleanup_test_environment() 