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
import tempfile
from pathlib import Path
from typing import Dict, Optional, AsyncGenerator, Generator
from dreamos.core.utils.file_utils import ensure_dir, clean_dir
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.social.utils.log_manager import LogManager
from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus
from dreamos.core.agent_control.agent_cellphone import AgentCellphone
from dreamos.core.bridge.chatgpt_bridge import ChatGPTBridge
from dreamos.core.shared.processors import MessageProcessor
from tests.utils.test_environment import TestEnvironment

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
def test_env() -> TestEnvironment:
    """Create a test environment for integration tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def log_dir(test_env: TestEnvironment) -> Path:
    """Get log directory for tests."""
    log_dir = test_env.get_test_dir("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

@pytest.fixture
def runtime_dir(test_env: TestEnvironment) -> Path:
    """Get runtime directory for tests."""
    runtime_dir = test_env.get_test_dir("runtime")
    runtime_dir.mkdir(exist_ok=True)
    return runtime_dir

@pytest.fixture
def clean_log_dir(test_env: TestEnvironment) -> Path:
    """Get clean test log directory."""
    log_dir = test_env.get_test_dir("logs")
    for file in log_dir.glob("*"):
        if file.is_file():
            file.unlink()
    return log_dir

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

@pytest_asyncio.fixture
async def temp_outbox_dir() -> AsyncGenerator[Path, None]:
    """Create a temporary directory for bridge outbox files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        outbox_dir = Path(temp_dir) / "bridge_outbox"
        outbox_dir.mkdir()
        yield outbox_dir

@pytest.fixture
def mock_agent_ops() -> AgentOperations:
    """Create a mock agent operations interface."""
    return AgentOperations(
        runtime_dir=Path("runtime"),
        config=TEST_CONFIG
    )

@pytest.fixture
def mock_agent_status() -> AgentStatus:
    """Create a mock agent status tracker."""
    return AgentStatus(
        status_file=Path("runtime/agent_status/status.json"),
        config=TEST_CONFIG
    )

@pytest.fixture
def mock_agent_cellphone() -> AgentCellphone:
    """Create a mock agent cellphone."""
    return AgentCellphone(
        config=TEST_CONFIG
    )

@pytest.fixture
def mock_chatgpt_bridge() -> ChatGPTBridge:
    """Create a mock ChatGPT bridge."""
    return ChatGPTBridge(
        config=TEST_CONFIG
    )

@pytest.fixture
def mock_message_processor() -> MessageProcessor:
    """Create a mock message processor."""
    return MessageProcessor(
        runtime_dir=Path("runtime")
    )

@pytest.fixture
def temp_outbox():
    """Create a temporary outbox directory for testing."""
    outbox_dir = Path("data/bridge_outbox")
    ensure_dir(outbox_dir)
    yield outbox_dir
    clean_dir(outbox_dir) 