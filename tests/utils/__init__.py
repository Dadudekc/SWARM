import pytest
from pathlib import Path
from typing import Dict, Any
import tempfile
import json
from unittest.mock import AsyncMock

def create_temp_config(config_data: Dict[str, Any]) -> Path:
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        json.dump(config_data, f)
        return Path(f.name)

def cleanup_temp_file(file_path: Path):
    """Clean up a temporary file."""
    try:
        file_path.unlink()
    except Exception:
        pass

@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
    return {
        "agent_id": "test_agent",
        "capabilities": ["test", "mock"],
        "description": "A test agent for unit testing",
        "name": "Test Agent",
        "settings": {
            "max_messages": 100,
            "retry_attempts": 3,
            "timeout": 30
        }
    }

# EDIT START: Add Discord test mocks for test_discord_commands.py
class MockMessage:
    """Minimal mock for discord.Message."""
    def __init__(self, content="", attachments=None):
        self.content = content
        self.attachments = attachments or []

class MockMember:
    """Minimal mock for discord.Member."""
    pass

class MockChannel:
    """Minimal mock for discord.TextChannel."""
    pass

class MockGuild:
    """Minimal mock for discord.Guild."""
    pass

class MockContext:
    """Minimal mock for discord.ext.commands.Context."""
    def __init__(self, message=None):
        self.message = message or MockMessage()
        self.send = lambda *a, **kw: None
        self.response = AsyncMock()
        self.response.edit_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.response.send_message = AsyncMock()

class MockBot:
    """Minimal mock for discord.ext.commands.Bot."""
    def __init__(self):
        self.agent_resume = None


def create_mock_embed(*args, **kwargs):
    """Return a dummy object for discord.Embed."""
    class DummyEmbed:
        title = ""
    return DummyEmbed()

def run_async_test(coro):
    """Run an async coroutine for testing."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)

def mock_discord_file(filename):
    """Return a dummy file-like object for discord.File."""
    class DummyFile:
        def __init__(self, name):
            self.filename = name
    return DummyFile(filename)
# EDIT END 