"""
Pytest Configuration
-----------------
Global test configuration and fixtures.
"""

import os
import sys
import pytest
import tempfile
import shutil
import gc
import time
from pathlib import Path
from typing import Generator, Dict, Any
import importlib
from types import SimpleNamespace
from tests.utils.test_environment import TestEnvironment

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create test directories
TEST_ROOT = Path(__file__).parent
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

# Ensure test directories exist
for dir_path in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR, TEST_CONFIG_DIR, VOICE_QUEUE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

def safe_delete(path: Path, retries: int = 3, delay: float = 0.2) -> None:
    """Safely delete a file with retries and GC flush.
    
    Args:
        path: Path to file to delete
        retries: Number of retry attempts
        delay: Delay between retries in seconds
    """
    for _ in range(retries):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            gc.collect()  # Force garbage collection
            time.sleep(delay)
    
    # Last attempt (force Windows handle release)
    try:
        os.remove(str(path))
    except Exception as e:
        print(f"[WARN] Could not delete {path}: {e}")

# Mock data
MOCK_AGENT_CONFIG = {
    "name": "TestAgent",
    "type": "test",
    "config": {
        "enabled": True,
        "priority": 1
    }
}

MOCK_PROMPT = "Test prompt"
MOCK_DEVLOG = "Test devlog entry"

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for all tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture(scope="session")
def test_dirs(test_env: TestEnvironment) -> dict[str, Path]:
    """Get all test directories."""
    return {
        "temp": test_env.get_test_dir("temp"),
        "runtime": test_env.get_test_dir("runtime"),
        "config": test_env.get_test_dir("config"),
        "data": test_env.get_test_dir("data"),
        "logs": test_env.get_test_dir("logs"),
        "output": test_env.get_test_dir("output"),
        "archive": test_env.get_test_dir("archive"),
        "failed": test_env.get_test_dir("failed"),
        "voice_queue": test_env.get_test_dir("voice_queue"),
        "report": test_env.get_test_dir("report"),
        "quarantine": test_env.get_test_dir("quarantine")
    }

@pytest.fixture(scope="session")
def test_config(test_env: TestEnvironment) -> Path:
    """Get test configuration file."""
    config_path = test_env.get_test_dir("config") / "test_config.json"
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text('{"test": true}')
    return config_path

@pytest.fixture
def clean_test_dirs(test_env: TestEnvironment):
    """Create a clean test directory structure."""
    return test_env

@pytest.fixture
def temp_dir(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    yield test_env.get_test_dir("temp")

@pytest.fixture
def test_config_dir(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Create a temporary directory with test configuration files."""
    config_dir = test_env.get_test_dir("config")
    
    # Create test response_loop_config.json
    response_loop_config = {
        "agent_id": "test_agent",
        "status": "active",
        "last_update": "2024-01-01T00:00:00Z",
        "config_version": "1.0"
    }
    test_env.create_test_config("response_loop_config.json", response_loop_config)
    
    # Create test agent_config.json
    agent_config = {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "type": "worker",
        "capabilities": ["task_processing", "status_reporting"]
    }
    test_env.create_test_config("agent_config.json", agent_config)
    
    return config_dir

@pytest.fixture(scope="function")
def test_file(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Test file in temporary directory."""
    test_file = test_env.create_test_file("test.txt")
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_json(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Test JSON file in temporary directory."""
    test_file = test_env.create_test_file("test.json")
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_yaml(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Test YAML file in temporary directory."""
    test_file = test_env.create_test_file("test.yaml")
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_log_dir(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Test log directory."""
    log_dir = test_env.get_test_dir("logs")
    yield log_dir
    if log_dir.exists():
        for file in log_dir.glob("*"):
            if file.is_file():
                safe_delete(file)

@pytest.fixture(scope="function")
def test_bridge_outbox(test_env: TestEnvironment) -> Generator[Path, None, None]:
    """Test bridge outbox directory."""
    outbox = test_env.get_test_dir("output") / "bridge_outbox"
    outbox.mkdir(exist_ok=True)
    yield outbox
    if outbox.exists():
        for file in outbox.glob("*"):
            if file.is_file():
                safe_delete(file)
        outbox.rmdir()

@pytest.fixture(scope="function")
def mock_message() -> Dict[str, Any]:
    """Mock message for testing."""
    return {
        "id": "test-123",
        "type": "test",
        "content": "Test message",
        "priority": "NORMAL",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@pytest.fixture(scope="function")
def mock_agent() -> Dict[str, Any]:
    """Mock agent for testing."""
    return {
        "id": "agent-123",
        "name": "Test Agent",
        "status": "active",
        "capabilities": ["test"]
    }

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(items):
    """Modify test items during collection."""
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)

    # Skip Windows-specific tests on non-Windows platforms
    if os.name != 'nt':
        skip_windows = pytest.mark.skip(reason="Windows-specific test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows) 
