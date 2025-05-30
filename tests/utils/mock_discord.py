"""
Mock Discord objects for testing.
"""

from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any
import asyncio
import io

class MockMessage:
    """Mock Discord message object."""
    def __init__(self, content: str = "", author: Any = None):
        self.content = content
        self.author = author or MagicMock()
        self.channel = MagicMock()
        self.guild = MagicMock()

class MockChannel:
    """Mock Discord channel object."""
    def __init__(self, name: str = "test-channel", id: int = 123456789):
        self.name = name
        self.id = id
        self.guild = MagicMock()

class MockGuild:
    """Mock Discord guild object."""
    def __init__(self, name: str = "test-guild", id: int = 987654321):
        self.name = name
        self.id = id
        self.channels = [MockChannel()]
        self.members = [MagicMock()]

class MockUser:
    """Mock Discord user object."""
    def __init__(self, name: str = "test-user", id: int = 111222333):
        self.name = name
        self.id = id
        self.display_name = name
        self.mention = f"<@{id}>"

class MockMember:
    """Mock Discord member object."""
    def __init__(self, name: str = "test-member", id: int = 444555666):
        self.name = name
        self.id = id
        self.display_name = name
        self.mention = f"<@{id}>"
        self.guild = MockGuild()
        self.roles = [MagicMock()]
        self.joined_at = MagicMock()
        self.status = "online"
        self.activity = None

class MockContext:
    """Mock Discord command context."""
    def __init__(self):
        self.message = MockMessage()
        self.channel = MockChannel()
        self.guild = MockGuild()
        self.author = MockUser()
        self.bot = MagicMock()
        self.command = MagicMock()
        self.prefix = "!"
        self.invoked_with = "test_command"
        self.invoked_subcommand = None
        self.subcommand_passed = None
        self.command_failed = False
        self.response = MagicMock()
        self.response.edit_message = AsyncMock()
        self.response.send_message = AsyncMock()
        
    async def send(self, content: str = None, **kwargs) -> MockMessage:
        """Mock context.send method. Returns a new MockMessage."""
        if hasattr(self.channel, 'send') and isinstance(self.channel.send, MagicMock):
            await self.channel.send(content, **kwargs)
        return MockMessage(content=content or "")
        
    async def reply(self, content: str = None, **kwargs) -> MockMessage:
        """Mock context.reply method. Returns a new MockMessage."""
        if hasattr(self.message, 'reply') and isinstance(self.message.reply, MagicMock):
            await self.message.reply(content, **kwargs)
        return MockMessage(content=content or "")

class MockBot:
    """Mock Discord bot object."""
    def __init__(self, name: str = "test-bot", id: int = 999888777):
        self.name = name
        self.id = id
        self.user = MagicMock(name="MockUser")
        self.loop = MagicMock()
        self.commands = []
        self.add_command = MagicMock()
        self.remove_command = MagicMock()
        self.get_command = MagicMock()
        self.guilds = [MockGuild()]
        self.voice_clients = []
        self.latency = 0.0
        self.is_ready = MagicMock(return_value=True)
        self.wait_until_ready = MagicMock()
        self.close = MagicMock()
        self.logout = MagicMock()

def create_mock_context() -> Dict[str, Any]:
    """Create a mock context for Discord commands."""
    return {
        "message": MockMessage(),
        "channel": MockChannel(),
        "guild": MockGuild(),
        "author": MockUser(),
        "bot": MagicMock()
    }

def create_mock_embed(title: str = "Test Embed", description: str = "Test Description", **kwargs) -> MagicMock:
    """Create a mock Discord embed object.
    
    Args:
        title: Embed title
        description: Embed description
        **kwargs: Additional embed attributes
        
    Returns:
        Mock embed object
    """
    embed = MagicMock()
    embed.title = title
    embed.description = description
    embed.color = kwargs.get("color", 0x000000)
    embed.fields = kwargs.get("fields", [])
    embed.footer = kwargs.get("footer", MagicMock())
    embed.thumbnail = kwargs.get("thumbnail", MagicMock())
    embed.image = kwargs.get("image", MagicMock())
    embed.author = kwargs.get("author", MagicMock())
    embed.timestamp = kwargs.get("timestamp", None)
    embed.url = kwargs.get("url", None)
    
    # Add methods
    embed.add_field = MagicMock()
    embed.set_footer = MagicMock()
    embed.set_thumbnail = MagicMock()
    embed.set_image = MagicMock()
    embed.set_author = MagicMock()
    
    return embed

def run_async_test(coro):
    """Run an async test coroutine.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def mock_discord_file(filename: str = "test.txt", content: str = "test content") -> MagicMock:
    """Create a mock Discord file object.
    
    Args:
        filename: Name of the file
        content: Content of the file
        
    Returns:
        Mock file object
    """
    file = MagicMock()
    file.filename = filename
    file.content = content.encode()
    file.size = len(content)
    file.fp = io.BytesIO(content.encode())
    file.close = MagicMock()
    file.seek = MagicMock()
    file.read = MagicMock(return_value=content.encode())
    return file 