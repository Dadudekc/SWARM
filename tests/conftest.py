"""
Pytest Configuration
-----------------
Global test configuration and fixtures.
"""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

# Test directory constants
TEST_ROOT = Path("tests")
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

@pytest.fixture(scope="session")
def test_env() -> Dict[str, str]:
    """Test environment variables."""
    return {
        "DREAMOS_TEST_MODE": "1",
        "DREAMOS_TEST_DATA_DIR": str(TEST_DATA_DIR.absolute()),
        "DREAMOS_TEST_CACHE_DIR": str(Path("test_cache").absolute())
    }

@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture(scope="function")
def test_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Test file in temporary directory."""
    test_file = temp_dir / "test.txt"
    yield test_file
    if test_file.exists():
        test_file.unlink()

@pytest.fixture(scope="function")
def test_json(temp_dir: Path) -> Generator[Path, None, None]:
    """Test JSON file in temporary directory."""
    test_file = temp_dir / "test.json"
    yield test_file
    if test_file.exists():
        test_file.unlink()

@pytest.fixture(scope="function")
def test_yaml(temp_dir: Path) -> Generator[Path, None, None]:
    """Test YAML file in temporary directory."""
    test_file = temp_dir / "test.yaml"
    yield test_file
    if test_file.exists():
        test_file.unlink()

@pytest.fixture(scope="function")
def test_log_dir(temp_dir: Path) -> Generator[Path, None, None]:
    """Test log directory."""
    log_dir = temp_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    yield log_dir
    if log_dir.exists():
        for file in log_dir.glob("*"):
            if file.is_file():
                file.unlink()
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
                file.unlink()
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

@pytest.fixture(scope="function")
def clean_test_dirs() -> None:
    """Clean test directories before each test."""
    for dir_path in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR, VOICE_QUEUE_DIR]:
        if dir_path.exists():
            for file in dir_path.glob("*"):
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    for subfile in file.glob("**/*"):
                        if subfile.is_file():
                            subfile.unlink()
                    file.rmdir()

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