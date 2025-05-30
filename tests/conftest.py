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
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch
import tempfile
import shutil
import yaml
import json
from datetime import datetime, timedelta
import gzip

from tests.utils.gui_test_utils import is_headless_environment, should_skip_gui_test
from tests.test_config import setup_test_environment, cleanup_test_environment
from tests.utils.test_utils import (
    safe_remove, TEST_ROOT, TEST_DATA_DIR, TEST_OUTPUT_DIR,
    VOICE_QUEUE_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR,
    ensure_test_dirs
)

# Filter out Discord audioop deprecation warning
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="'audioop' is deprecated and slated for removal in Python 3.13",
    module="discord.player"
)

# Mock pyautogui to prevent actual key presses during tests
sys.modules['pyautogui'] = MagicMock()

# Suppress PyQt5 sipPyTypeDict deprecation warnings
warnings.filterwarnings(
    "ignore",
    message="sipPyTypeDict.*is deprecated"
)

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Mock agent configuration
MOCK_AGENT_CONFIG = {
    "name": "test_agent",
    "type": "test",
    "config": {
        "test_param": "test_value"
    }
}

@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs() -> Generator[None, None, None]:
    """Set up test directories and clean them up after tests."""
    # Create test directories
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Clean up test directories
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)

@pytest.fixture(scope="function")
def clean_test_dirs() -> Generator[None, None, None]:
    """Clean test directories before and after each test."""
    # Clean up before test
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Clean up after test
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)

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
def mock_pyautogui() -> Generator[None, None, None]:
    """Mock PyAutoGUI functions for headless testing."""
    if is_headless_environment():
        with patch('pyautogui.size', return_value=(1920, 1080)), \
             patch('pyautogui.position', return_value=(0, 0)), \
             patch('pyautogui.moveTo'), \
             patch('pyautogui.click'), \
             patch('pyautogui.doubleClick'), \
             patch('pyautogui.rightClick'), \
             patch('pyautogui.dragTo'), \
             patch('pyautogui.scroll'), \
             patch('pyautogui.hotkey'), \
             patch('pyautogui.press'), \
             patch('pyautogui.write'), \
             patch('pyautogui.screenshot', return_value=MagicMock()):
            yield
    else:
        yield

@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for each test."""
    temp_dir = TEST_TEMP_DIR / f"test_{next(tempfile._get_candidate_names())}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    safe_remove(temp_dir)

@pytest.fixture(scope="function")
def temp_log_dir(temp_dir) -> Generator[Path, None, None]:
    """Create a temporary log directory for each test."""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    yield log_dir

@pytest.fixture
def mock_config():
    return {
        "log_dir": "logs",
        "max_size": 10 * 1024 * 1024,  # 10MB
        "max_age": 30 * 24 * 60 * 60,  # 30 days
        "use_json": True,
        "use_text": True,
        "use_temp_dir": True,  # Use temp dir for tests
        "batch_size": 100,
        "batch_timeout": 5,
        "rotation_check_interval": 60,
        "compress_after": 1
    }

@pytest.fixture
def log_config(mock_config):
    return LogConfig(**mock_config)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ['DISCORD_TOKEN'] = 'test_token'
    os.environ['VOICE_CHANNEL_ID'] = '123456789'
    yield
    # Cleanup
    if 'DISCORD_TOKEN' in os.environ:
        del os.environ['DISCORD_TOKEN']
    if 'VOICE_CHANNEL_ID' in os.environ:
        del os.environ['VOICE_CHANNEL_ID']

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI interaction"
    )
    config.option.asyncio_mode = "strict"
    config.option.asyncio_default_fixture_loop_scope = "function"

def pytest_collection_modifyitems(items):
    """Modify test items to skip GUI tests in headless environments."""
    for item in items:
        if "gui" in item.keywords and should_skip_gui_test():
            item.add_marker(pytest.mark.skip(reason="GUI tests skipped in headless environment"))
        if "asyncio" in item.keywords:
            item.add_marker(pytest.mark.asyncio)

@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    data_dir = Path(project_root) / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

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

@pytest.fixture
def clean_runtime_dir():
    """Create and clean up runtime directory."""
    path = TEST_RUNTIME_DIR
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(exist_ok=True)
    yield path
    shutil.rmtree(path)

@pytest.fixture(autouse=True)
async def setup_teardown():
    """Global setup and teardown for all tests."""
    # Setup
    temp_dir = TEST_TEMP_DIR
    temp_dir.mkdir(exist_ok=True)
    
    yield
    
    # Teardown
    safe_remove(temp_dir)

@pytest.fixture
def voice_queue(tmp_path):
    """Create a temporary voice queue directory."""
    queue = tmp_path / "voice_queue"
    queue.mkdir(exist_ok=True)
    return queue

@pytest.fixture
def bot() -> discord.Client:
    """Create a mock bot instance."""
    return MagicMock(spec=discord.Client)

@pytest_asyncio.fixture(autouse=True)
async def setup_teardown():
    """Set up and tear down the test environment."""
    setup_test_environment()
    yield
    cleanup_test_environment()

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configuration files."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def temp_runtime_dir(temp_dir) -> Generator[Path, None, None]:
    """Create a temporary runtime directory for each test."""
    runtime_dir = temp_dir / "runtime"
    runtime_dir.mkdir()
    mailbox_dir = runtime_dir / "mailbox"
    mailbox_dir.mkdir()
    yield runtime_dir
    safe_remove(runtime_dir)

@pytest.fixture(scope="function")
def message_processor(temp_runtime_dir):
    """Create test message processor instance."""
    from dreamos.core.messaging.message_processor import MessageProcessor
    return MessageProcessor(base_path=temp_runtime_dir, runtime_dir=temp_runtime_dir)

@pytest.fixture(scope="function")
def agent_operations(temp_runtime_dir):
    """Create test agent operations instance."""
    from dreamos.core.agent_control.agent_operations import AgentOperations
    return AgentOperations(runtime_dir=temp_runtime_dir)

@pytest.fixture(scope="session")
def temp_voice_dir():
    """Create a temporary directory for voice files."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)

@pytest.fixture(scope="session")
def mock_driver_manager():
    """Mock the driver manager to prevent actual browser launches."""
    with patch('social.core.driver_manager.DriverManager') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.get_multi_driver_sessions.return_value = {
            'facebook': MagicMock(),
            'twitter': MagicMock(),
            'instagram': MagicMock(),
            'reddit': MagicMock(),
            'linkedin': MagicMock(),
            'stocktwits': MagicMock()
        }
        yield mock_instance

@pytest.fixture(scope="function")
def mock_dispatcher(mock_driver_manager):
    """Create a mock dispatcher instance."""
    from social.core.dispatcher import TaskDispatcher
    dispatcher = TaskDispatcher(mock_driver_manager)
    return dispatcher

@pytest.fixture(scope="function")
def mock_rate_limiter():
    """Create a mock rate limiter instance."""
    from social.utils.rate_limiter import RateLimiter
    limiter = RateLimiter()
    return limiter

@pytest.fixture(scope="function")
def mock_platform_strategy():
    """Create a mock platform strategy instance."""
    from social.strategies.platform_strategy_base import PlatformStrategy
    strategy = PlatformStrategy(
        driver=MagicMock(),
        config=mock_config(),
        memory_update={},
        agent_id="test_agent",
        log_manager=MagicMock()
    )
    return strategy

@pytest.fixture
def gui_test_env():
    """Fixture to set up GUI test environment."""
    if is_headless_environment():
        pytest.skip("GUI tests require a display")
    
    # Additional GUI test setup can be added here
    yield
    
    # Cleanup after GUI tests
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    except ImportError:
        pass

@pytest.fixture
def mock_agent_config() -> Dict[str, Any]:
    """Return a mock agent configuration."""
    return MOCK_AGENT_CONFIG.copy()

@pytest.fixture
def test_log_dir() -> Path:
    """Create a temporary log directory for testing."""
    log_dir = TEST_RUNTIME_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    yield log_dir
    if log_dir.exists():
        shutil.rmtree(log_dir)

@pytest.fixture
def mock_log_data() -> Dict[str, Any]:
    """Provide mock log data for testing."""
    return {
        "level": "INFO",
        "message": "Test log message",
        "metadata": {"test": True},
        "platform": "test",
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def mock_log_file(test_log_dir: Path) -> Path:
    """Create a mock log file for testing."""
    log_file = test_log_dir / "test.log"
    with open(log_file, "w") as f:
        json.dump({
            "level": "INFO",
            "message": "Test log message",
            "metadata": {"test": True},
            "platform": "test",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }, f)
    return log_file

@pytest.fixture
def mock_old_log_file(test_log_dir: Path) -> Path:
    """Create a mock old log file for testing."""
    old_date = datetime.now() - timedelta(days=2)
    log_file = test_log_dir / f"old_{old_date.strftime('%Y%m%d')}.log"
    with open(log_file, "w") as f:
        json.dump({
            "level": "INFO",
            "message": "Old test log message",
            "metadata": {"test": True},
            "platform": "test",
            "status": "success",
            "timestamp": old_date.isoformat()
        }, f)
    return log_file

@pytest.fixture
def mock_compressed_log_file(test_log_dir: Path) -> Path:
    """Create a mock compressed log file for testing."""
    log_file = test_log_dir / "test.log.gz"
    with gzip.open(log_file, "wt") as f:
        json.dump({
            "level": "INFO",
            "message": "Compressed test log message",
            "metadata": {"test": True},
            "platform": "test",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }, f)
    return log_file

@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup():
    """Set up test environment before tests and clean up after."""
    setup_test_environment()
    yield
    cleanup_test_environment()

@pytest.fixture(scope="function")
def temp_log_dir() -> Path:
    """Create a temporary log directory for each test."""
    log_dir = Path("tests/runtime/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    yield log_dir 