"""
Test suite for Discord bot commands.
"""

import unittest
import asyncio
import discord
from discord.ext import commands
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import os
import json
from pathlib import Path
import types
from datetime import datetime
import shutil
from typing import Dict, Any, Optional

from tests.utils.mock_discord import (
    MockMessage, MockMember, MockChannel, MockGuild,
    MockContext, MockBot, create_mock_embed, run_async_test,
    Command
)
from tests.utils.test_utils import (
    cleanup_test_environment,
    TEST_DATA_DIR, TEST_CONFIG_DIR, MOCK_AGENT_CONFIG,
    MOCK_PROMPT, MOCK_DEVLOG
)
from tests.conftest import (
    TEST_ROOT, TEST_DATA_DIR, TEST_CONFIG_DIR, TEST_RUNTIME_DIR,
    MOCK_AGENT_CONFIG, clean_test_dirs
)

# Import the commands we want to test
from discord_bot.cogs.basic import BasicCommands
from discord_bot.discord_commands import AgentCommands
from dreamos.core.messaging.enums import MessageMode

# Mark all tests in this module as Discord tests
pytestmark = pytest.mark.discord

@pytest.mark.asyncio
class TestBasicCommands:
    """Test the basic commands functionality."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_test_environment_fixture, mock_log_manager):
        """Set up test environment."""
        self.bot = MockBot()
        self.ctx = MockContext()
        self.commands = BasicCommands(self.bot, mock_log_manager)
        yield
        cleanup_test_environment()
    
    async def test_help_command(self):
        """Test the help command."""
        await self.commands.help_command(self.ctx)
        self.ctx.send.assert_called_once()
        assert isinstance(self.ctx.send.call_args[0][0], discord.Embed)
    
    async def test_status_command(self):
        """Test the status command."""
        await self.commands.status(self.ctx)
        self.ctx.send.assert_called_once()
        assert isinstance(self.ctx.send.call_args[0][0], discord.Embed)
    
    async def test_task_command(self):
        """Test the task command."""
        await self.commands.task(self.ctx, "test_task")
        self.ctx.send.assert_called_once()
        assert isinstance(self.ctx.send.call_args[0][0], discord.Embed)
    
    async def test_devlog_command(self):
        """Test the devlog command."""
        await self.commands.devlog(self.ctx, "info", "Test message")
        self.ctx.send.assert_called_once()
        assert "Logged info message" in self.ctx.send.call_args[0][0]

@pytest.mark.asyncio
class TestAgentCommands:
    """Test the agent command functionality."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_test_environment_fixture, mock_log_manager):
        """Set up test environment."""
        self.bot = MockBot()
        self.bot.agent_resume = AsyncMock()
        self.bot.agent_resume.coords = {"Agent-1": {}, "Agent-2": {}}
        self.bot.agent_resume.send_message = AsyncMock(return_value=True)
        self.bot.agent_resume.get_agent_devlog = AsyncMock(return_value="Test devlog content")
        self.bot.agent_resume.clear_agent_devlog = AsyncMock(return_value=True)
        
        # Patch AgentCommands.send_command at the class level
        patcher = patch.object(AgentCommands, 'send_command', new_callable=AsyncMock)
        self.addCleanup = getattr(self, 'addCleanup', lambda f: None)  # for unittest compatibility
        self.send_command_patch = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Mock coordinate loading with test file
        with patch('dreamos.core.coordinate_manager.CoordinateManager._load_coordinates') as mock_load:
            mock_load.return_value = {
                "Agent-1": {
                    "input_box": (100, 100),
                    "initial_spot": (200, 200),
                    "copy_button": (300, 300)
                },
                "Agent-2": {
                    "input_box": (400, 400),
                    "initial_spot": (500, 500),
                    "copy_button": (600, 600)
                }
            }
            self.commands = AgentCommands(self.bot)
            # Patch the instance's send_command after instantiation
            self.commands.send_command = AsyncMock(side_effect=lambda *args, **kwargs: True)
        
        # Patch process_message with an actual async function
        async def always_true(*args, **kwargs):
            return True
        self.commands.message_processor.process_message = types.MethodType(always_true, self.commands.message_processor)
        
        # Mock log manager
        self.commands.log_manager = AsyncMock()
        self.commands.log_manager.log = AsyncMock(return_value=True)
        self.commands.log_manager.get_log = AsyncMock(return_value="Test log content")
        self.commands.log_manager.clear_log = AsyncMock(return_value=True)
        
        # Use the real MessageMode enum
        self.commands.MessageMode = MessageMode
        
        self.ctx = MockContext()
        self.ctx.send = AsyncMock()
        yield
        cleanup_test_environment()
    
    async def test_help_command(self):
        """Test the help command."""
        await self.commands.show_help.callback(self.commands, self.ctx)
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args
        args, kwargs = call_args[0], call_args[1]
        embed = args[0] if args else kwargs.get('embed')
        view = args[1] if len(args) > 1 else kwargs.get('view')
        assert isinstance(embed, discord.Embed)
        assert isinstance(view, discord.ui.View)
    
    async def test_list_agents(self):
        """Test listing available agents."""
        await self.commands.list_agents.callback(self.commands, self.ctx)
        self.ctx.send.assert_called_once()
        assert isinstance(self.ctx.send.call_args[0][0], discord.Embed)
    
    async def test_send_prompt(self):
        """Test sending a prompt to an agent."""
        await self.commands.send_prompt.callback(self.commands, self.ctx, "Agent-1", "Test prompt")
        self.ctx.send.assert_called_once()
        assert "Prompt sent" in self.ctx.send.call_args[0][0]
    
    async def test_update_log(self):
        """Test updating agent log."""
        await self.commands.update_log.callback(self.commands, self.ctx, "Agent-1", "Test log")
        self.ctx.send.assert_called_once()
        assert "Log updated" in self.ctx.send.call_args[0][0]
    
    async def test_view_log(self):
        """Test viewing agent log."""
        await self.commands.view_log.callback(self.commands, self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        assert "Test log content" in self.ctx.send.call_args[0][0]
    
    async def test_clear_log(self):
        """Test clearing agent log."""
        await self.commands.clear_log.callback(self.commands, self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        assert "Log cleared" in self.ctx.send.call_args[0][0]

@pytest.fixture
def mock_bot():
    """Create a mock bot for testing."""
    bot = MockBot()
    bot.orchestrator = AsyncMock()
    bot.log_manager = AsyncMock()
    return bot

@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    ctx = MockContext()
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = AsyncMock()
    orchestrator.get_status = AsyncMock(return_value={
        "status": "running",
        "components": {
            "agent": "active",
            "voice": "active",
            "discord": "active"
        }
    })
    return orchestrator

@pytest.fixture
def mock_log_manager():
    """Create a mock log manager for testing."""
    log_manager = AsyncMock()
    log_manager.log = AsyncMock(return_value=True)
    return log_manager

@pytest.mark.asyncio
async def test_help_command(mock_bot, mock_context, mock_orchestrator, mock_log_manager):
    """Test help command with mocked dependencies."""
    commands = BasicCommands(mock_bot, mock_log_manager)
    await commands.help_command(mock_context)
    mock_context.send.assert_called_once()
    assert isinstance(mock_context.send.call_args[0][0], discord.Embed)

@pytest.mark.asyncio
async def test_status_command(mock_bot, mock_context, mock_orchestrator, mock_log_manager):
    """Test status command with mocked dependencies."""
    commands = BasicCommands(mock_bot, mock_log_manager)
    await commands.status(mock_context)
    mock_context.send.assert_called_once()
    assert isinstance(mock_context.send.call_args[0][0], discord.Embed)

@pytest.mark.asyncio
async def test_task_command(mock_bot, mock_context, mock_orchestrator, mock_log_manager):
    """Test task command with mocked dependencies."""
    commands = BasicCommands(mock_bot, mock_log_manager)
    await commands.task(mock_context, "test_task")
    mock_context.send.assert_called_once()
    assert isinstance(mock_context.send.call_args[0][0], discord.Embed)

@pytest.mark.asyncio
async def test_devlog_command(mock_bot, mock_context, mock_orchestrator, mock_log_manager):
    """Test devlog command with mocked dependencies."""
    commands = BasicCommands(mock_bot, mock_log_manager)
    await commands.devlog(mock_context, "info", "Test message")
    mock_context.send.assert_called_once()
    assert "Logged info message" in mock_context.send.call_args[0][0] 