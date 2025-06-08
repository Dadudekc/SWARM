"""
Integration Test Configuration
---------------------------
Configuration for integration tests.

This module provides fixtures and configuration for integration tests,
including test environment setup and cleanup.
"""

import os
import pytest
from pathlib import Path
from dreamos.core.utils.file_utils import ensure_dir, clean_dir

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

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment."""
    # Create test directories
    test_dirs = [
        "data/bridge_outbox",
        "data/archive",
        "data/failed",
        "data/runtime/memory",
        "logs"
    ]
    
    for dir_path in test_dirs:
        ensure_dir(dir_path)
    
    yield
    
    # Clean up test directories
    for dir_path in test_dirs:
        if Path(dir_path).exists():
            clean_dir(dir_path)

@pytest.fixture
def temp_outbox():
    """Create a temporary outbox directory for testing."""
    outbox_dir = Path("data/bridge_outbox")
    ensure_dir(outbox_dir)
    yield outbox_dir
    clean_dir(outbox_dir) 