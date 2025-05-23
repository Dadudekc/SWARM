"""
Test utilities for Discord bot tests.
"""

import asyncio
import discord
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, List, Dict, Any
import io

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
        guild: Optional[discord.Guild] = None,
        create_guild: bool = True
    ):
        self.id = id
        self.name = name
        self.guild = guild
        if create_guild and not guild:
            self.guild = MockGuild(channels=[self])
        self.mention = f"<#{id}>"

class MockMember:
    """Mock Discord member for testing."""
    def __init__(
        self,
        name: str = "TestUser",
        id: int = 111222333,
        roles: List[discord.Role] = None,
        guild: Optional[discord.Guild] = None
    ):
        self.name = name
        self.id = id
        self.roles = roles or []
        self.mention = f"<@{id}>"
        self.display_name = name
        self.guild = guild or MockGuild()

class MockMessage:
    """Mock Discord message for testing."""
    def __init__(
        self,
        content: str,
        author: Optional[discord.Member] = None,
        channel: Optional[discord.TextChannel] = None,
        attachments: List[discord.Attachment] = None
    ):
        self.content = content
        self.author = author or MockMember()
        self.channel = channel or MockChannel(guild=self.author.guild)
        self.attachments = attachments or []
        self.id = 123456789
        self.guild = self.author.guild

class MockContext:
    """Mock Discord context for testing."""
    def __init__(
        self,
        message: Optional[MockMessage] = None,
        bot: Optional[discord.Client] = None
    ):
        self.message = message or MockMessage("!help")
        self.bot = bot or MockBot()
        self.send = AsyncMock()
        self.typing = AsyncMock()
        self.typing.__aenter__ = AsyncMock()
        self.typing.__aexit__ = AsyncMock()
        self.author = self.message.author
        self.channel = self.message.channel
        self.guild = self.message.guild

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

def mock_discord_file(
    filename: str,
    content: bytes = b"test content"
) -> discord.File:
    """Create a mock Discord file for testing."""
    file = MagicMock()
    file.filename = filename
    file.content = content
    file.read = AsyncMock(return_value=content)
    return file 