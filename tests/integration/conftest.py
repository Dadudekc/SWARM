"""
Integration Test Configuration
---------------------------
Configuration for integration tests.

This module provides fixtures and configuration for integration tests,
including test environment setup and cleanup.
"""

import os
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Optional
from dreamos.core.utils.file_utils import ensure_dir, clean_dir
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.social.utils.log_manager import LogManager

# Set test environment variables
os.environ["CHATGPT_API_KEY"] = "test-api-key"
os.environ["DISCORD_TOKEN"] = "test-discord-token"

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )

@pytest.fixture(scope="session")
def test_log_config():
    """Create test log configuration."""
    log_dir = Path("runtime/test_logs")
    ensure_dir(log_dir)
    
    config = LogConfig(
        log_dir=str(log_dir),
        level=LogLevel.DEBUG,
        file_path=str(log_dir / "test.log"),
        log_to_file=True,
        log_to_console=True,
        platforms={"test": "test.log"}
    )
    
    return config

@pytest.fixture(scope="session")
def test_log_manager(test_log_config):
    """Create test log manager."""
    return LogManager(config=test_log_config)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    # Set test mode
    os.environ["DREAMOS_TEST_MODE"] = "1"
    
    # Create test directories
    ensure_dir(Path("runtime/test_logs"))
    ensure_dir(Path("runtime/test_data"))
    
    yield
    
    # Cleanup
    clean_dir(Path("runtime/test_logs"))
    clean_dir(Path("runtime/test_data"))

@pytest.fixture
def temp_outbox():
    """Create a temporary outbox directory for testing."""
    outbox_dir = Path("data/bridge_outbox")
    ensure_dir(outbox_dir)
    yield outbox_dir
    clean_dir(outbox_dir) 