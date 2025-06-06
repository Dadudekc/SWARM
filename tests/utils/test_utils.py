"""
Test utilities and helper functions.
"""

import os
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union

# Test directory constants
TEST_ROOT = Path("tests")
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

# Mock configuration for testing
MOCK_AGENT_CONFIG = {
    "agent_id": "test-agent",
    "message_queue_path": "tests/data/messages/queue.json",
    "log_level": "DEBUG",
    "inbox_path": "tests/data/agent_comms/test-agent/inbox.json",
    "devlog_path": "tests/data/agent_comms/test-agent/devlog.md",
    "settings": {
        "retry_attempts": 3,
        "timeout": 5,
        "max_message_size": 1024,
        "cleanup_interval": 3600
    }
}

# Mock test data
MOCK_PROMPT = "This is a test prompt for unit testing."
MOCK_RESPONSE = "This is a test response for unit testing."

MOCK_DEVLOG = "This is a test devlog entry for unit testing."

def ensure_test_dirs() -> None:
    """Ensure all test directories exist."""
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_CONFIG_DIR, 
                     TEST_RUNTIME_DIR, TEST_TEMP_DIR, VOICE_QUEUE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def safe_remove(path: Union[str, Path]) -> None:
    """Safely remove a file or directory."""
    path = Path(path)
    if path.exists():
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove a directory."""
    path = Path(path)
    if path.exists():
        if recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

def get_test_file_path(filename: str, directory: Optional[Path] = None) -> Path:
    """Get path to a test file."""
    if directory is None:
        directory = TEST_DATA_DIR
    return directory / filename

def create_test_file(filename: str, content: str = "", directory: Optional[Path] = None) -> Path:
    """Create a test file with content."""
    path = get_test_file_path(filename, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return path

def cleanup_test_files() -> None:
    """Clean up all test files and directories."""
    for directory in [TEST_OUTPUT_DIR, TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)

def cleanup_test_environment():
    """Remove test directories."""
    test_dirs = [
        "tests/data",
        "tests/output",
        "tests/config",
        "tests/runtime",
        "tests/temp",
        "tests/voice/queue"
    ]
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

class MockMember:
    def __init__(
        self,
        id: int = 123456789,
        name: str = "test-user",
        roles: List[Any] = None,
        bot: bool = False
    ):
        self.id = id
        self.name = name
        self.roles = roles or []
        self.bot = bot
        self.mention = f"<@{id}>" 