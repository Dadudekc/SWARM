"""
Test Utilities Module

Common utilities and mocks for testing.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock

# Test root directory
TEST_ROOT = Path(__file__).parent.parent
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_TMP_DIR = TEST_ROOT / "tmp"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

def ensure_test_dirs():
    """Ensure all test directories exist."""
    for dir_path in [TEST_CONFIG_DIR, TEST_DATA_DIR, TEST_TMP_DIR, 
                    TEST_OUTPUT_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR,
                    VOICE_QUEUE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def test_output_dir() -> Path:
    """Get the test output directory."""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_OUTPUT_DIR

def safe_remove(path: Path):
    """Safely remove a file or directory."""
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            for child in path.iterdir():
                safe_remove(child)
            path.rmdir()
    except Exception as e:
        print(f"Warning: Failed to remove {path}: {e}")

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