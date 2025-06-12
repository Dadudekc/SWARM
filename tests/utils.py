"""
Test Utilities Module

Common utilities and mocks for testing.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock
import pytest
from tests.utils.test_environment import TestEnvironment

# Test directory constants
TEST_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

# Ensure test directories exist
for dir_path in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR, TEST_CONFIG_DIR, VOICE_QUEUE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

def create_mock_agent(agent_id: str = "test_agent") -> AsyncMock:
    """Create a mock agent.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        Mock agent instance
    """
    agent = AsyncMock()
    agent.agent_id = agent_id
    agent.get_status.return_value = {"status": "active"}
    return agent

def create_mock_bridge() -> AsyncMock:
    """Create a mock bridge.
    
    Returns:
        Mock bridge instance
    """
    bridge = AsyncMock()
    bridge.process_message.return_value = "Mocked response"
    return bridge

def create_mock_cellphone() -> AsyncMock:
    """Create a mock cellphone.
    
    Returns:
        Mock cellphone instance
    """
    cellphone = AsyncMock()
    cellphone.inject_prompt.return_value = True
    return cellphone

def create_mock_message_processor() -> AsyncMock:
    """Create a mock message processor.
    
    Returns:
        Mock message processor instance
    """
    processor = AsyncMock()
    processor.process_message.return_value = True
    return processor

def create_temp_outbox() -> Path:
    """Create a temporary outbox directory.
    
    Returns:
        Path to temporary outbox directory
    """
    temp_dir = tempfile.mkdtemp()
    outbox_dir = Path(temp_dir) / "bridge_outbox"
    outbox_dir.mkdir()
    return outbox_dir

def write_test_message(outbox_path: Path, agent_id: str, content: str) -> None:
    """Write a test message to the outbox.
    
    Args:
        outbox_path: Path to outbox directory
        agent_id: ID of the agent
        content: Message content
    """
    message_path = outbox_path / f"agent-{agent_id}.json"
    with open(message_path, 'w') as f:
        json.dump({
            "content": content,
            "timestamp": "2024-01-01T00:00:00Z"
        }, f)

def read_test_message(outbox_path: Path, agent_id: str) -> Optional[Dict]:
    """Read a test message from the outbox.
    
    Args:
        outbox_path: Path to outbox directory
        agent_id: ID of the agent
        
    Returns:
        Message dictionary or None if not found
    """
    message_path = outbox_path / f"agent-{agent_id}.json"
    if not message_path.exists():
        return None
        
    with open(message_path, 'r') as f:
        return json.load(f)

def ensure_test_dirs():
    """Ensure all test directories exist."""
    for dir_path in [TEST_OUTPUT_DIR, TEST_DATA_DIR, TEST_CONFIG_DIR, 
                    TEST_RUNTIME_DIR, TEST_TEMP_DIR, VOICE_QUEUE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def test_output_dir():
    """Get test output directory."""
    return TEST_OUTPUT_DIR 

def safe_remove(path):
    """Stub for safe file removal."""
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except Exception:
        pass 

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for utility tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def temp_dir(test_env: TestEnvironment) -> Path:
    """Get temporary directory for tests."""
    return test_env.get_test_dir("temp")

@pytest.fixture
def outbox_dir(test_env: TestEnvironment) -> Path:
    """Get test outbox directory."""
    outbox_dir = test_env.get_test_dir("output") / "bridge_outbox"
    outbox_dir.mkdir(exist_ok=True)
    return outbox_dir

@pytest.fixture
def test_file(test_env: TestEnvironment) -> Path:
    """Create a test file."""
    file_path = test_env.get_test_dir("temp") / "test.txt"
    file_path.write_text("test content")
    return file_path

@pytest.fixture
def test_dir(test_env: TestEnvironment) -> Path:
    """Create a test directory."""
    dir_path = test_env.get_test_dir("temp") / "test_dir"
    dir_path.mkdir(exist_ok=True)
    return dir_path

__all__ = [
    "TEST_ROOT",
    "TEST_DATA_DIR",
    "TEST_OUTPUT_DIR",
    "TEST_CONFIG_DIR",
    "TEST_RUNTIME_DIR",
    "TEST_TEMP_DIR",
    "VOICE_QUEUE_DIR",
    "ensure_test_dirs",
    "test_output_dir",
    "create_temp_outbox",
    "safe_remove",
    "create_mock_agent",
    "create_mock_bridge",
    "create_mock_cellphone",
    "create_mock_message_processor",
    "write_test_message",
    "read_test_message"
] 