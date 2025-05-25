"""
Pytest configuration and common fixtures.
"""

import pytest
import pytest_asyncio
import logging
import os
import sys
import warnings
from pathlib import Path
import asyncio
import discord
from typing import Generator
from unittest.mock import MagicMock, patch
import tempfile
import shutil

# Filter out Discord audioop deprecation warning
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="'audioop' is deprecated and slated for removal in Python 3.13",
    module="discord.player"
)

# Mock pyautogui to prevent actual key presses during tests
sys.modules['pyautogui'] = MagicMock()

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield

@pytest.fixture(autouse=True)
def mock_pyautogui():
    """Mock pyautogui to prevent actual key presses during tests."""
    with patch('pyautogui.press') as mock_press, \
         patch('pyautogui.hotkey') as mock_hotkey, \
         patch('pyautogui.write') as mock_write, \
         patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.click') as mock_click:
        yield {
            'press': mock_press,
            'hotkey': mock_hotkey,
            'write': mock_write,
            'moveTo': mock_move,
            'click': mock_click
        }

# Test data directory
@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

# Mock agent registry
@pytest.fixture
def mock_agent_registry():
    """Provide a mock agent registry for testing."""
    return {
        "Agent-1": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-2": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-3": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-4": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-5": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-6": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-7": {"status": "active", "capabilities": ["messaging", "tasks"]},
        "Agent-8": {"status": "active", "capabilities": ["messaging", "tasks"]}
    }

# Test message templates
@pytest.fixture
def test_messages():
    """Provide test message templates."""
    return {
        "welcome": "Welcome to Dream.OS! You are now part of our agent network.",
        "task": "Please complete the following task: {task_description}",
        "status": "Current status: {status}",
        "error": "Error occurred: {error_message}",
        "warning": "Warning: {warning_message}",
        "info": "Information: {info_message}"
    }

# Test configuration
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "max_message_length": 1000,
        "max_priority": 5,
        "rate_limit": 100,  # messages per minute
        "retry_attempts": 3,
        "retry_delay": 1.0,  # seconds
        "cleanup_interval": 3600,  # seconds
        "history_size": 1000
    }

@pytest.fixture
def bot() -> discord.Client:
    """Create a mock bot instance."""
    return MagicMock(spec=discord.Client)

@pytest_asyncio.fixture(autouse=True)
async def setup_teardown():
    """Set up and tear down the test environment."""
    from .test_config import setup_test_environment, cleanup_test_environment
    setup_test_environment()
    yield
    cleanup_test_environment()

# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest-asyncio."""
    config.option.asyncio_mode = "strict"
    config.option.asyncio_default_fixture_loop_scope = "function"

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir) 