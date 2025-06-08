"""
Test suite for Discord bot help menu.
"""

import pytest
import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

from tests.utils.mock_discord import (
    MockMessage, MockMember, MockChannel, MockGuild,
    MockContext, MockBot, create_mock_embed, run_async_test,
    Command
)

@pytest.fixture
def mock_bot():
    """Create a mock Discord bot instance."""
    bot = MockBot()
    # Add orchestrator mock
    bot.orchestrator = MagicMock()
    bot.orchestrator.get_status = AsyncMock(return_value={
        "status": "Operational",
        "components": {
            "Core": "Online",
            "Messaging": "Online"
        }
    })
    return bot

@pytest.fixture
def mock_context():
    """Create a mock Discord context."""
    ctx = MockContext()
    # Set up send method to return a mock message
    mock_message = MagicMock()
    ctx.send = AsyncMock(return_value=mock_message)
    return ctx

@pytest.mark.asyncio
async def test_help_command_no_args(mock_bot, mock_context):
    """Test help command with no arguments."""
    from discord_bot.cogs.help_menu import HelpMenu
    
    # Add some test cogs and commands
    mock_bot.cogs = {
        "TestCog": MagicMock(
            get_commands=lambda: [
                MagicMock(name="test1", help="Test command 1", hidden=False),
                MagicMock(name="test2", help="Test command 2", hidden=False)
            ]
        )
    }
    
    cog = HelpMenu(mock_bot)
    await cog.help_command(mock_context)
    
    mock_context.send.assert_called_once()
    args, kwargs = mock_context.send.call_args
    assert isinstance(args[0], discord.Embed)

@pytest.mark.asyncio
async def test_help_command_with_command(mock_bot, mock_context):
    """Test help command with a specific command."""
    from discord_bot.cogs.help_menu import HelpMenu
    
    # Create a test command
    test_cmd = MagicMock(
        name="test",
        help="Test command description",
        aliases=["t"],
        signature="<arg>"
    )
    mock_bot.get_command = MagicMock(return_value=test_cmd)
    
    cog = HelpMenu(mock_bot)
    await cog.help_command(mock_context, "test")
    
    mock_context.send.assert_called_once()
    args, kwargs = mock_context.send.call_args
    assert isinstance(args[0], discord.Embed)

@pytest.mark.asyncio
async def test_ping_command(mock_bot, mock_context):
    """Test ping command."""
    from discord_bot.cogs.help_menu import HelpMenu
    
    cog = HelpMenu(mock_bot)
    await cog.ping(mock_context)
    
    mock_context.send.assert_called_once()
    args, kwargs = mock_context.send.call_args
    assert "Pong!" in args[0]

@pytest.mark.asyncio
async def test_status_command(mock_bot, mock_context):
    """Test status command."""
    from discord_bot.cogs.help_menu import HelpMenu
    
    cog = HelpMenu(mock_bot)
    await cog.status(mock_context)
    
    mock_context.send.assert_called_once()
    args, kwargs = mock_context.send.call_args
    assert isinstance(args[0], discord.Embed)

@pytest.mark.asyncio
async def test_about_command(mock_bot, mock_context):
    """Test about command."""
    from discord_bot.cogs.help_menu import HelpMenu
    
    cog = HelpMenu(mock_bot)
    await cog.about(mock_context)
    
    mock_context.send.assert_called_once()
    args, kwargs = mock_context.send.call_args
    assert isinstance(args[0], discord.Embed) 
