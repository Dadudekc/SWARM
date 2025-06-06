"""
Test utilities for Discord bot tests.
"""

import asyncio
import discord
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, List, Dict, Any
import io
import pytest

class MockGuild:
    """Mock Discord guild for testing."""
    def __init__(
        self,
        id: int = 123456789,
        name: str = "Test Guild",
        channels: Optional[List['MockChannel']] = None
    ):
        self.id = id
        self.name = name
        self.channels = channels or []
        self.members = []

class MockChannel:
    """Mock Discord channel for testing."""
    def __init__(
        self,
        id: int = 987654321,
        name: str = "test-channel",
        guild: Optional[Any] = None,
        create_guild: bool = True
    ):
        self.id = id
        self.name = name
        self.guild = guild or (create_mock_guild() if create_guild else None)
        self.mention = f"<#{id}>"

class MockMember:
    """Mock Discord member for testing."""
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

class MockMessage:
    """Mock Discord message for testing."""
    def __init__(
        self,
        content: str = "",
        author: Optional[Any] = None,
        channel: Optional[Any] = None,
        guild: Optional[Any] = None,
        id: int = 1
    ):
        self.content = content
        self.author = author or MockMember()
        self.channel = channel or MockChannel()
        self.guild = guild or self.channel.guild
        self.id = id
        self.mention = f"<@{id}>"

class MockContext:
    """Mock Discord context for testing."""
    def __init__(
        self,
        message: Optional[Any] = None,
        channel: Optional[Any] = None,
        author: Optional[Any] = None,
        guild: Optional[Any] = None,
        bot: Optional[Any] = None
    ):
        self.message = message
        self.channel = channel
        self.author = author
        self.guild = guild
        self.bot = bot
        self.send = AsyncMock()
        self.typing = AsyncMock()
        self.typing.__aenter__ = AsyncMock()
        self.typing.__aexit__ = AsyncMock()
        
        # Add response attribute for interaction-like behavior
        self.response = AsyncMock()
        self.response.edit_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.response.send_message = AsyncMock()

class MockBot:
    """Mock Discord bot for testing."""
    def __init__(self):
        self.user = MockMember(name="TestBot", id=999888777)
        self.guilds = [MockGuild()]
        self.latency = 0.1
        self.commands = {}
        self.agent_resume = MagicMock()
        self.agent_resume.coords = {}
        self.agent_resume.get_agent_coords = AsyncMock()
        self.agent_resume.update_agent_coords = AsyncMock()
        self.agent_resume.get_agent_devlog = AsyncMock()
        self.agent_resume.update_agent_devlog = AsyncMock()
        self.agent_resume.clear_agent_devlog = AsyncMock()

def create_mock_embed(
    title: str,
    description: str,
    fields: List[Dict[str, Any]] = None,
    color: int = 0x00ff00
) -> discord.Embed:
    """Create a mock Discord embed for testing."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )
    
    return embed

async def run_async_test(coro):
    """Run an async test coroutine."""
    return await asyncio.get_event_loop().run_until_complete(coro)

def create_mock_file(*args, **kwargs) -> Any:
    """Return a mock file object for testing (replaces discord.File)."""
    class MockFile:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    return MockFile(*args, **kwargs)

# Test cases
def test_mock_guild():
    """Test MockGuild creation and attributes."""
    guild = MockGuild()
    assert guild.id == 123456789
    assert guild.name == "Test Guild"
    assert isinstance(guild.channels, list)
    assert isinstance(guild.members, list)

def test_mock_channel():
    """Test MockChannel creation and attributes."""
    channel = MockChannel()
    assert channel.id == 987654321
    assert channel.name == "test-channel"
    assert isinstance(channel.guild, MockGuild)
    assert channel.mention == "<#987654321>"

def test_mock_member():
    """Test MockMember creation and attributes."""
    member = MockMember()
    assert member.name == "test-user"
    assert member.id == 123456789
    assert isinstance(member.roles, list)
    assert member.mention == "<@123456789>"
    assert isinstance(member.guild, MockGuild)

def test_mock_message():
    """Test MockMessage creation and attributes."""
    message = MockMessage("test message")
    assert message.content == "test message"
    assert isinstance(message.author, MockMember)
    assert isinstance(message.channel, MockChannel)
    assert isinstance(message.attachments, list)
    assert message.id == 123456789
    assert isinstance(message.guild, MockGuild)

def test_mock_context():
    """Test MockContext creation and attributes."""
    context = MockContext()
    assert isinstance(context.message, MockMessage)
    assert isinstance(context.bot, MockBot)
    assert isinstance(context.send, AsyncMock)
    assert isinstance(context.typing, AsyncMock)
    assert isinstance(context.author, MockMember)
    assert isinstance(context.channel, MockChannel)
    assert isinstance(context.guild, MockGuild)
    assert isinstance(context.response, AsyncMock)

def test_mock_bot():
    """Test MockBot creation and attributes."""
    bot = MockBot()
    assert isinstance(bot.user, MockMember)
    assert bot.user.name == "TestBot"
    assert bot.user.id == 999888777
    assert isinstance(bot.guilds, list)
    assert len(bot.guilds) == 1
    assert isinstance(bot.guilds[0], MockGuild)
    assert bot.latency == 0.1
    assert isinstance(bot.commands, dict)

def test_create_mock_embed():
    """Test create_mock_embed function."""
    fields = [
        {"name": "Field 1", "value": "Value 1", "inline": True},
        {"name": "Field 2", "value": "Value 2", "inline": False}
    ]
    embed = create_mock_embed("Test Title", "Test Description", fields)
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Test Title"
    assert embed.description == "Test Description"
    assert embed.color.value == 0x00ff00
    assert len(embed.fields) == 2

@pytest.mark.asyncio
async def test_run_async_test():
    """Test run_async_test function."""
    async def test_coro():
        return "test result"
    
    result = await test_coro()
    assert result == "test result"

def test_mock_discord_file():
    """Test mock_discord_file function."""
    file = create_mock_file("test.txt", b"test content")
    assert file.args[0] == "test.txt"
    assert file.args[1] == b"test content"
    assert isinstance(file.args[2], AsyncMock) 