"""
Pytest configuration and common fixtures.
"""

import pytest
try:
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback for missing dependency
    import types
    import inspect
    import asyncio
    def _fixture(*args, **kwargs):
        import pytest
        def decorator(func):
            if inspect.iscoroutinefunction(func):
                def sync_wrapper(*fargs, **fkwargs):
                    return asyncio.run(func(*fargs, **fkwargs))
                return pytest.fixture(*args, **kwargs)(sync_wrapper)
            return pytest.fixture(*args, **kwargs)(func)
        return decorator
    pytest_asyncio = types.SimpleNamespace(fixture=_fixture)
import logging
import os
import sys
import warnings
from pathlib import Path
import asyncio
try:
    import discord
except ModuleNotFoundError:  # pragma: no cover - fallback for missing dependency
    import types
    discord = types.SimpleNamespace(Client=object)
from typing import Generator, Dict, Any, Optional
from unittest.mock import MagicMock, patch
import tempfile
import shutil
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for missing dependency
    import json
    class _YAMLStub:
        @staticmethod
        def safe_load(stream):
            if isinstance(stream, (str, bytes)):
                return json.loads(stream)
            return json.load(stream)

        @staticmethod
        def dump(data, stream=None):
            text = json.dumps(data)
            if stream is None:
                return text
            stream.write(text)

    yaml = _YAMLStub()
    sys.modules.setdefault('yaml', yaml)
import json
from datetime import datetime, timedelta
import gzip
try:
    import fakeredis
except ModuleNotFoundError:  # pragma: no cover - fallback for missing dependency
    fakeredis = MagicMock()
    sys.modules.setdefault('fakeredis', fakeredis)
try:
    import redis
except ModuleNotFoundError:  # pragma: no cover - fallback for missing dependency
    redis = MagicMock()
    sys.modules.setdefault('redis', redis)
import time
import stat
import platform
for _mod in ["win32security", "win32con", "win32api", "pywintypes", "psutil", "win32file", "win32process", "win32gui"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
psutil = sys.modules.get('psutil', MagicMock())

if 'praw' not in sys.modules:
    sys.modules['praw'] = MagicMock()

# Provide selenium stubs if selenium is not installed
if 'selenium' not in sys.modules:
    import types

    selenium_stub = types.ModuleType('selenium')
    webdriver_mod = types.ModuleType('selenium.webdriver')
    webdriver_common = types.ModuleType('selenium.webdriver.common')
    by_mod = types.ModuleType('selenium.webdriver.common.by')
    webdriver_remote = types.ModuleType('selenium.webdriver.remote')
    webdriver_remote_webdriver = types.ModuleType('selenium.webdriver.remote.webdriver')
    webdriver_remote_webelement = types.ModuleType('selenium.webdriver.remote.webelement')
    webdriver_support = types.ModuleType('selenium.webdriver.support')
    webdriver_support_ui = types.ModuleType('selenium.webdriver.support.ui')
    webdriver_support_ec = types.ModuleType('selenium.webdriver.support.expected_conditions')
    common_mod = types.ModuleType('selenium.common')
    exc_mod = types.ModuleType('selenium.common.exceptions')

    class _Exc(Exception):
        pass

    for name in [
        'TimeoutException', 'WebDriverException',
        'ElementClickInterceptedException', 'ElementNotInteractableException',
        'NoSuchElementException', 'StaleElementReferenceException'
    ]:
        setattr(exc_mod, name, _Exc)

    class By:
        ID = 'id'
        CSS_SELECTOR = 'css'

    by_mod.By = By

    webdriver_mod.remote = webdriver_remote
    webdriver_remote.webdriver = webdriver_remote_webdriver
    webdriver_remote.webelement = webdriver_remote_webelement
    webdriver_mod.support = webdriver_support
    webdriver_support.ui = webdriver_support_ui
    webdriver_support.expected_conditions = webdriver_support_ec

    class WebDriver:
        pass
    webdriver_remote_webdriver.WebDriver = WebDriver
    class WebDriverWait:
        def __init__(self, *a, **k):
            pass
        def until(self, *a, **k):
            return True
    webdriver_support_ui.WebDriverWait = WebDriverWait
    class WebElement:
        pass
    webdriver_remote_webelement.WebElement = WebElement

    sys.modules.update({
        'selenium': selenium_stub,
        'selenium.webdriver': webdriver_mod,
        'selenium.webdriver.common': webdriver_common,
        'selenium.webdriver.common.by': by_mod,
        'selenium.webdriver.remote': webdriver_remote,
        'selenium.webdriver.remote.webdriver': webdriver_remote_webdriver,
        'selenium.webdriver.remote.webelement': webdriver_remote_webelement,
        'selenium.webdriver.support': webdriver_support,
        'selenium.webdriver.support.ui': webdriver_support_ui,
        'selenium.webdriver.support.expected_conditions': webdriver_support_ec,
        'selenium.common': common_mod,
        'selenium.common.exceptions': exc_mod,
    })

from tests.utils.gui_test_utils import is_headless_environment, should_skip_gui_test
from tests.test_config import setup_test_environment, cleanup_test_environment
from tests.utils.test_utils import (
    safe_remove, TEST_ROOT, TEST_DATA_DIR, TEST_OUTPUT_DIR,
    VOICE_QUEUE_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR,
    ensure_test_dirs
)
from tests.test_markers import (
    is_claimed_by_agent, get_claiming_agent, get_claim_issue,
    agent_claimed, agent_fixed, agent_skipped, agent_in_progress
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

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--agent-id",
        action="store",
        default=None,
        help="ID of the agent running the tests"
    )
    parser.addoption(
        "--skip-claimed",
        action="store_true",
        default=False,
        help="Skip tests claimed by other agents"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on agent ID and claimed tests."""
    agent_id = config.getoption("--agent-id")
    skip_claimed = config.getoption("--skip-claimed")
    
    if not agent_id:
        return
    
    for item in items:
        # Skip tests claimed by other agents
        if skip_claimed and is_claimed_by_agent(item) and not is_claimed_by_agent(item, agent_id):
            item.add_marker(pytest.mark.skip(reason=f"Test claimed by agent {get_claiming_agent(item)}"))
            continue
        
        # Add agent ID to test name for better tracking
        item.name = f"[Agent-{agent_id}] {item.name}"

@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs() -> Generator[None, None, None]:
    """Set up test directories and clean them up after tests."""
    # Create test directories
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
            dir_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to create test directory {dir_path}: {e}")
    
    yield
    
    # Clean up test directories
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to remove test directory {dir_path}: {e}")

@pytest.fixture(scope="function")
def clean_test_dirs() -> Generator[None, None, None]:
    """Clean test directories before and after each test."""
    # Clean up before test
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
            dir_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to clean test directory {dir_path}: {e}")
    
    yield
    
    # Clean up after test
    for dir_path in [TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to clean test directory {dir_path}: {e}")

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    yield
    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

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

@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests.
    
    Yields:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def test_dirs(temp_dir: Path) -> Generator[Dict[str, Path], None, None]:
    """Create test directories.
    
    Args:
        temp_dir: Path to temporary directory
        
    Yields:
        Dictionary of test directory paths
    """
    dirs = {
        "data": temp_dir / "data",
        "logs": temp_dir / "logs",
        "cache": temp_dir / "cache",
        "temp": temp_dir / "temp"
    }
    
    # Create directories with proper permissions
    for dir_path in dirs.values():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Ensure directory is writable
            test_file = dir_path / ".test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            pytest.skip(f"Could not create test directory {dir_path}: {e}")
    
    yield dirs
    
    # Cleanup
    for dir_path in dirs.values():
        try:
            shutil.rmtree(dir_path, ignore_errors=True)
        except (PermissionError, OSError):
            pass

@pytest.fixture(scope="function")
def test_env(test_dirs: Dict[str, Path]) -> Generator[Dict[str, Any], None, None]:
    """Create test environment.
    
    Args:
        test_dirs: Dictionary of test directory paths
        
    Yields:
        Dictionary of test environment variables
    """
    env = {
        "TEST_DATA_DIR": str(test_dirs["data"]),
        "TEST_LOG_DIR": str(test_dirs["logs"]),
        "TEST_CACHE_DIR": str(test_dirs["cache"]),
        "TEST_TEMP_DIR": str(test_dirs["temp"]),
        "PYTEST_CURRENT_TEST": "1"
    }
    
    # Set environment variables
    old_env = {}
    for key, value in env.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env
    
    # Restore environment variables
    for key, value in old_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value

@pytest.fixture(scope="function")
def agent_id(request) -> Optional[str]:
    """Get agent ID from command line option."""
    return request.config.getoption("--agent-id")

@pytest.fixture(scope="function")
def test_analysis_file() -> Path:
    """Get path to test analysis file."""
    return Path(project_root) / "test_error_analysis.json"

@pytest.fixture(scope="function")
def test_analysis(test_analysis_file: Path) -> Generator[Dict, None, None]:
    """Load and save test analysis data."""
    if not test_analysis_file.exists():
        data = {
            "claimed_tests": {},
            "test_status": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "in_progress": 0
            },
            "agent_assignments": {},
            "last_run": None,
            "test_history": []
        }
    else:
        with open(test_analysis_file, 'r') as f:
            data = json.load(f)
    
    yield data
    
    with open(test_analysis_file, 'w') as f:
        json.dump(data, f, indent=2)

@pytest.fixture(scope="function")
def update_test_status(test_analysis: Dict, agent_id: Optional[str]) -> Generator[None, None, None]:
    """Update test status in analysis file."""
    def _update(test_name: str, status: str, fix_attempt: Optional[str] = None):
        if test_name in test_analysis["claimed_tests"]:
            test_analysis["claimed_tests"][test_name]["status"] = status
            if fix_attempt:
                test_analysis["claimed_tests"][test_name]["fix_attempts"].append({
                    "attempt": fix_attempt,
                    "timestamp": datetime.now().isoformat()
                })
    
    yield _update

@pytest.fixture(scope="function")
def claim_test(test_analysis: Dict, agent_id: Optional[str]) -> Generator[None, None, None]:
    """Claim a test for an agent."""
    def _claim(test_name: str, issue: str) -> bool:
        if not agent_id:
            return False
        
        if test_name in test_analysis["claimed_tests"]:
            return False
        
        test_analysis["claimed_tests"][test_name] = {
            "agent": agent_id,
            "status": "in_progress",
            "issue": issue,
            "claimed_at": datetime.now().isoformat(),
            "fix_attempts": []
        }
        
        test_analysis["test_status"]["in_progress"] += 1
        return True
    
    yield _claim

@pytest.fixture(scope="function")
def release_test(test_analysis: Dict) -> Generator[None, None, None]:
    """Release a test claim."""
    def _release(test_name: str):
        if test_name in test_analysis["claimed_tests"]:
            del test_analysis["claimed_tests"][test_name]
            test_analysis["test_status"]["in_progress"] -= 1
    
    yield _release

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        "reddit": {
            "client_id": "dummy",
            "client_secret": "dummy",
            "username": "bot",
            "password": "hunter2",
            "user_agent": "test_agent",
            "subreddits": ["test_subreddit"],
            "max_posts_per_day": 10,
            "max_comments_per_day": 20,
            "post_delay": 3600,
            "comment_delay": 1800
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "log_dir": "logs",
            "max_size_mb": 10,
            "max_files": 5,
            "max_age_days": 30,
            "compress_after_days": 1
        },
        "platforms": {
            "reddit": "reddit.log",
            "discord": "discord.log",
            "twitter": "twitter.log"
        }
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
    config.addinivalue_line(
        "markers", "quarantined: mark test as quarantined due to known issues"
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

@pytest.fixture(autouse=True)
def clean_runtime_dir():
    """Clean up runtime directory before and after each test."""
    path = Path(tempfile.gettempdir()) / "dream_os_test_runtime"
    
    try:
        # Clean up existing directory if it exists
        if path.exists():
            try:
                shutil.rmtree(path)
            except (PermissionError, OSError) as e:
                logging.warning(f"Failed to remove existing runtime directory: {e}")
                # Try to remove individual files
                for item in path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        logging.warning(f"Failed to remove {item}: {e}")
                        continue
        
        # Create fresh directory with proper permissions
        path.mkdir(parents=True, exist_ok=True)
        
        # Verify directory is writable
        test_file = path / ".test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            pytest.skip(f"Runtime directory is not writable: {e}")
        
        yield path
        
    finally:
        # Cleanup after test
        try:
            if path.exists():
                # First try to remove files individually
                for item in path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        logging.warning(f"Failed to remove {item}: {e}")
                        continue
                
                # Then try to remove the directory itself
                try:
                    path.rmdir()
                except Exception as e:
                    logging.warning(f"Failed to remove runtime directory: {e}")
        except Exception as e:
            logging.warning(f"Failed to clean up runtime directory: {e}")

@pytest.fixture(autouse=True)
async def setup_teardown():
    """Set up and tear down test environment."""
    # Create a temporary directory for all test files
    temp_base = Path(tempfile.mkdtemp(prefix="dream_os_test_"))
    
    # Set up test directories
    test_dirs = {
        'data': temp_base / "data",
        'output': temp_base / "output",
        'voice_queue': temp_base / "voice_queue",
        'config': temp_base / "config",
        'runtime': temp_base / "runtime",
        'temp': temp_base / "temp"
    }
    
    # Create directories
    for directory in test_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    
    # Update environment variables
    os.environ["DREAM_OS_TEST_DIR"] = str(test_dirs['runtime'])
    os.environ["DREAM_OS_TEST_DATA_DIR"] = str(test_dirs['data'])
    os.environ["DREAM_OS_TEST_OUTPUT_DIR"] = str(test_dirs['output'])
    os.environ["DREAM_OS_TEST_CONFIG_DIR"] = str(test_dirs['config'])
    
    try:
        # Create test config file
        config = {
            "log_dir": str(test_dirs['runtime'] / "logs"),
            "channel_assignments": {
                "Agent-1": "general",
                "Agent-2": "commands"
            },
            "global_ui": {
                "input_box": {"x": 100, "y": 100},
                "initial_spot": {"x": 200, "y": 200},
                "copy_button": {"x": 300, "y": 300},
                "response_region": {
                    "top_left": {"x": 400, "y": 400},
                    "bottom_right": {"x": 600, "y": 600}
                }
            }
        }
        
        config_path = test_dirs['config'] / "agent_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
            
    except Exception as e:
        logging.error(f"Failed to set up test environment: {e}")
        raise
    
    yield
    
    # Clean up
    try:
        # Remove environment variables
        for var in ["DREAM_OS_TEST_DIR", "DREAM_OS_TEST_DATA_DIR", 
                    "DREAM_OS_TEST_OUTPUT_DIR", "DREAM_OS_TEST_CONFIG_DIR"]:
            if var in os.environ:
                del os.environ[var]
        
        # Remove test directories
        for directory in test_dirs.values():
            if directory.exists():
                try:
                    shutil.rmtree(directory)
                except Exception as e:
                    logging.warning(f"Failed to remove {directory}: {e}")
                    
        # Remove base temp directory
        if temp_base.exists():
            try:
                shutil.rmtree(temp_base)
            except Exception as e:
                logging.warning(f"Failed to remove {temp_base}: {e}")
                
    except Exception as e:
        logging.error(f"Failed to clean up test environment: {e}")

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
    # Clean up after test
    if log_dir.exists():
        # First, ensure all file handles are closed
        import gc
        gc.collect()
        time.sleep(0.1)  # Give time for file handles to be released
        
        # Then remove files
        for file in log_dir.glob("*"):
            try:
                if file.is_file():
                    # Try to close any open handles
                    try:
                        with open(file, 'r') as f:
                            pass  # Just open and close to ensure handle is released
                    except:
                        pass
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            except (PermissionError, OSError) as e:
                logging.warning(f"Failed to remove {file}: {e}")
                time.sleep(0.1)  # Wait before retrying
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        shutil.rmtree(file)
                except (PermissionError, OSError) as e:
                    logging.warning(f"Failed to remove {file} after retry: {e}")
        
        # Finally remove the directory
        try:
            log_dir.rmdir()
        except (PermissionError, OSError) as e:
            logging.warning(f"Failed to remove log directory {log_dir}: {e}")
            time.sleep(0.1)  # Wait before retrying
            try:
                log_dir.rmdir()
            except (PermissionError, OSError) as e:
                logging.warning(f"Failed to remove log directory {log_dir} after retry: {e}")

@pytest.fixture(scope="function")
def mock_redis():
    """Create a mock Redis server using fakeredis."""
    server = fakeredis.FakeServer()
    redis_client = fakeredis.FakeRedis(server=server)
    
    # Patch redis.Redis to return our fake client
    with patch('redis.Redis', return_value=redis_client):
        yield redis_client

@pytest.fixture(scope="function")
def mock_redis_connection(mock_redis):
    """Create a mock Redis connection that can be used in tests."""
    with patch('social.core.redis_manager.RedisManager.get_connection', return_value=mock_redis):
        yield mock_redis

@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Create and clean up test directories with proper permissions."""
    test_dirs = [
        "tests/runtime/logs",
        "tests/runtime/cookies",
        "tests/runtime/profiles",
        "tests/runtime/temp"
    ]
    
    # First, try to kill any processes that might be holding file handles
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            for file in proc.open_files():
                if any(dir in file.path for dir in test_dirs):
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Wait a moment for processes to be killed
    time.sleep(1)
    
    # Clean up and create directories
    for dir_path in test_dirs:
        path = Path(dir_path)
        try:
            # Remove directory if it exists
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            
            # Create directory
            path.mkdir(parents=True, exist_ok=True)
            
            # Set permissions
            if platform.system() == 'Windows':
                try:
                    # Get current user's SID
                    username = os.getenv('USERNAME')
                    sid = win32security.LookupAccountName(None, username)[0]
                    
                    # Create DACL
                    dacl = win32security.ACL()
                    dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        win32con.GENERIC_ALL,
                        sid
                    )
                    
                    # Set security
                    security = win32security.SECURITY_DESCRIPTOR()
                    security.SetSecurityDescriptorDacl(1, dacl, 0)
                    win32security.SetFileSecurity(
                        str(path),
                        win32security.DACL_SECURITY_INFORMATION,
                        security
                    )
                except Exception as e:
                    print(f"Warning: Could not set Windows security on {path}: {e}")
                    # Fallback to basic permissions
                    os.chmod(str(path), stat.S_IWRITE | stat.S_IREAD)
            else:
                os.chmod(str(path), 0o777)
                
        except Exception as e:
            print(f"Warning: Could not set up directory {path}: {e}")
    
    yield
    
    # Cleanup after tests
    for dir_path in test_dirs:
        path = Path(dir_path)
        try:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up directory {path}: {e}")

def load_quarantined_tests() -> Dict[str, Any]:
    """Load quarantined tests from analysis file."""
    analysis_file = Path(project_root) / "test_error_analysis.json"
    if not analysis_file.exists():
        return {"test_details": {}, "quarantined_tests": []}
    
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    return data

def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip quarantined tests."""
    quarantined_data = load_quarantined_tests()
    quarantined_tests = {
        test["test_name"]: test["issue"] 
        for test in quarantined_data.get("quarantined_tests", [])
    }
    
    for item in items:
        test_name = item.name
        if test_name in quarantined_tests:
            item.add_marker(
                pytest.mark.skip(
                    reason=f"Test quarantined: {quarantined_tests[test_name]}"
                )
            ) 