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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    # No legacy test directories needed
    yield

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
        "log_level": "DEBUG",
        "max_retries": 3,
        "timeout": 5,
        "rate_limit": {
            "requests": 10,
            "period": 60
        }
    }

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

@pytest.fixture(scope="function")
def MOCK_AGENT_CONFIG() -> Dict[str, Any]:
    """Mock agent configuration for testing."""
    return {
        "id": "agent-123",
        "name": "Test Agent",
        "type": "test",
        "status": "active",
        "capabilities": ["test"],
        "config": {
            "log_level": "DEBUG",
            "max_retries": 3,
            "timeout": 5,
            "rate_limit": {
                "requests": 10,
                "period": 60
            }
        }
    }

def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "windows: marks tests as Windows-specific"
    )
    config.addinivalue_line(
        "markers",
        "pyqt5: marks tests that require PyQt5"
    )
    config.addinivalue_line(
        "markers",
        "swarm_core: marks tests that require swarm core functionality"
    )
    config.addinivalue_line(
        "markers",
        "bridge_integration: marks tests that require bridge integration"
    )
    config.addinivalue_line(
        "markers",
        "cellphone_pipeline: marks tests that require cellphone pipeline"
    )

def pytest_collection_modifyitems(items):
    """Modify test items."""
    # Skip Windows-specific tests on non-Windows platforms
    if os.name != 'nt':
        skip_windows = pytest.mark.skip(reason="Windows-specific test")
        for item in items:
            if "windows" in item.keywords:
                item.add_marker(skip_windows) 
