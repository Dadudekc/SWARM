"""
Mock Discord objects for testing.
"""

import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, List, Any

def command(name: Optional[str] = None, **kwargs):
    """Mock command decorator."""
    def decorator(func):
        func.name = name or func.__name__
        return func
    return decorator

# Add command decorator to commands namespace
commands.command = command

# Ensure Cog is available
if not hasattr(commands, 'Cog'):
    class Cog:
        """Mock Cog class."""
        def __init__(self, *args, **kwargs):
            pass
    commands.Cog = Cog

class MockMessage:
    """Mock Discord message."""
    
    def __init__(self, content: Optional[str] = None, attachments: Optional[List[Any]] = None, author: Optional[Any] = None):
        self.content = content
        self.attachments = attachments or []
        self.author = author or MockMember()

class MockMember:
    """Mock Discord member."""
    
    def __init__(self, name: str = "TestUser", id: int = 123456789):
        self.name = name
        self.id = id
        self.display_name = name

class MockChannel:
    """Mock Discord channel."""
    
    def __init__(self, name: str = "test-channel", id: int = 987654321):
        self.name = name
        self.id = id
        self.send = AsyncMock()

class MockGuild:
    """Mock Discord guild."""
    
    def __init__(self, name: str = "Test Guild", id: int = 123456789):
        self.name = name
        self.id = id

class MockContext:
    """Mock Discord context."""
    
    def __init__(self, message: Optional[MockMessage] = None, channel: Optional[MockChannel] = None, author: Optional[MockMember] = None):
        self.message = message or MockMessage()
        self.channel = channel or MockChannel()
        self.author = author or MockMember()
        self.send = AsyncMock()

class MockBot:
    """Mock Discord bot."""
    
    def __init__(self):
        self.commands = []
        self.cogs = {}
        self.event_handlers = {}
        self.agent_resume = AsyncMock()

def create_mock_embed(**kwargs) -> discord.Embed:
    """Create a mock embed."""
    return discord.Embed(**kwargs)

def mock_discord_file(filename: str) -> discord.File:
    """Create a mock Discord file."""
    return discord.File(filename)

async def run_async_test(coro):
    """Run an async test."""
    return await coro 