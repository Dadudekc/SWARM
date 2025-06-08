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

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test directories
TEST_ROOT = project_root / "tests"
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Create test directories
    TEST_DATA_DIR.mkdir(exist_ok=True)
    TEST_CONFIG_DIR.mkdir(exist_ok=True)
    TEST_RUNTIME_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup with safe deletion
    if TEST_DATA_DIR.exists():
        for file in TEST_DATA_DIR.glob("*"):
            safe_delete(file)
    if TEST_CONFIG_DIR.exists():
        for file in TEST_CONFIG_DIR.glob("*"):
            safe_delete(file)
    if TEST_RUNTIME_DIR.exists():
        for file in TEST_RUNTIME_DIR.glob("*"):
            safe_delete(file)

@pytest.fixture
def clean_test_dirs(tmp_path, monkeypatch):
    """
    Create a temporary directory for tests that need to write files.
    Monkeypatch any global paths so that tests operate under tmp_path.
    """
    test_root = tmp_path / "test_data"
    test_root.mkdir()

    # Monkeypatch any hardcoded base directories
    monkeypatch.setattr("dreamos.core.logging.log_config.get_log_path", lambda: str(test_root / "logs"))
    monkeypatch.setattr("dreamos.core.logging.log_config.get_metrics_path", lambda: str(test_root / "metrics"))

    yield test_root

    # After test, cleanup (pytest will auto-remove tmp_path)
    for child in test_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            safe_delete(child)

@pytest.fixture(scope="session")
def test_env() -> Dict[str, str]:
    """Test environment variables."""
    return {
        "DREAMOS_TEST_MODE": "1",
        "DREAMOS_TEST_DATA_DIR": str(TEST_DATA_DIR.absolute()),
        "DREAMOS_TEST_CACHE_DIR": str(Path("test_cache").absolute())
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def test_config_dir(temp_dir):
    """Create a temporary directory with test configuration files."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    
    # Create test response_loop_config.json
    response_loop_config = {
        "agent_id": "test_agent",
        "status": "active",
        "last_update": "2024-01-01T00:00:00Z",
        "config_version": "1.0"
    }
    (config_dir / "response_loop_config.json").write_text(
        str(response_loop_config)
    )
    
    # Create test agent_config.json
    agent_config = {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "type": "worker",
        "capabilities": ["task_processing", "status_reporting"]
    }
    (config_dir / "agent_config.json").write_text(
        str(agent_config)
    )
    
    return config_dir

@pytest.fixture(scope="function")
def test_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Test file in temporary directory."""
    test_file = temp_dir / "test.txt"
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_json(temp_dir: Path) -> Generator[Path, None, None]:
    """Test JSON file in temporary directory."""
    test_file = temp_dir / "test.json"
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_yaml(temp_dir: Path) -> Generator[Path, None, None]:
    """Test YAML file in temporary directory."""
    test_file = temp_dir / "test.yaml"
    yield test_file
    if test_file.exists():
        safe_delete(test_file)

@pytest.fixture(scope="function")
def test_log_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Test log directory."""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    yield log_dir
    if log_dir.exists():
        for file in log_dir.glob("*"):
            if file.is_file():
                safe_delete(file)
        log_dir.rmdir()

@pytest.fixture(scope="function")
def test_bridge_outbox(temp_dir: Path) -> Generator[Path, None, None]:
    """Test bridge outbox directory."""
    outbox = temp_dir / "bridge_outbox"
    outbox.mkdir(exist_ok=True)
    yield outbox
    if outbox.exists():
        for file in outbox.glob("*"):
            if file.is_file():
                safe_delete(file)
        outbox.rmdir()

@pytest.fixture(scope="function")
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "type": "worker",
        "capabilities": ["task_processing", "status_reporting"],
        "config": {
            "enabled": True,
            "priority": 1
        }
    }

@pytest.fixture(scope="function")
def mock_message() -> Dict[str, Any]:
    """Test message."""
    return {
        "message_id": "test_message_1",
        "content": "Test message content",
        "timestamp": "2024-01-01T00:00:00Z",
        "sender": "test_sender",
        "recipient": "test_recipient"
    }

@pytest.fixture(scope="function")
def mock_agent() -> Dict[str, Any]:
    """Test agent."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "type": "worker",
        "status": "active",
        "capabilities": ["task_processing", "status_reporting"]
    }

@pytest.fixture(scope="function")
def MOCK_AGENT_CONFIG() -> Dict[str, Any]:
    """Test agent configuration."""
    return {
        "name": "TestAgent",
        "type": "test",
        "config": {
            "enabled": True,
            "priority": 1
        }
    }

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )

def pytest_collection_modifyitems(items):
    """Modify test items."""
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow) 
