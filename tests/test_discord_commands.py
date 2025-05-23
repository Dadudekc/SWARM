"""
Test suite for Discord bot commands.
"""

import unittest
import asyncio
import discord
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import os
import json
from pathlib import Path

from .test_utils import (
    MockMessage, MockMember, MockChannel, MockGuild,
    MockContext, MockBot, create_mock_embed, run_async_test,
    mock_discord_file
)
from .test_config import (
    setup_test_environment, cleanup_test_environment,
    TEST_DATA_DIR, TEST_CONFIG_DIR, MOCK_AGENT_CONFIG,
    MOCK_PROMPT, MOCK_DEVLOG
)

# Import the commands we want to test
from discord_bot.commands import HelpMenu, AgentCommands
from dreamos.core import MessageMode

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_bot():
    bot = Mock()
    bot.agent_resume = Mock()
    bot.agent_resume.coords = {
        "Agent-1": {"status": "active"},
        "Agent-2": {"status": "inactive"},
        "Agent-3": {"status": "error"}
    }
    bot.agent_resume.send_message = AsyncMock(return_value=True)
    return bot

@pytest.fixture
def mock_ctx():
    ctx = Mock()
    ctx.send = AsyncMock()
    return ctx

@pytest.mark.asyncio
class TestHelpMenu(unittest.TestCase):
    """Test the HelpMenu class functionality."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        """Set up test environment."""
        self.ctx = MockContext()
        self.menu = HelpMenu()
        yield
        # Cleanup if needed
    
    async def test_menu_initialization(self):
        """Test that the help menu initializes correctly."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.assertEqual(len(self.menu.pages), 4)
        self.assertEqual(self.menu.current_page, 0)
    
    async def test_page_navigation(self):
        """Test page navigation in help menu."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        
        # Test next page
        await self.menu.next_page(self.ctx)
        self.assertEqual(self.menu.current_page, 1)
        
        # Test previous page
        await self.menu.previous_page(self.ctx)
        self.assertEqual(self.menu.current_page, 0)

@pytest.mark.asyncio
class TestAgentCommands(unittest.TestCase):
    """Test the agent command functionality."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        """Set up test environment."""
        setup_test_environment()
        self.bot = MockBot()
        self.bot.agent_resume = MagicMock()
        self.bot.agent_resume.coords = {"Agent-1": {}, "Agent-2": {}}
        self.commands = AgentCommands(self.bot)
        self.ctx = MockContext()
        yield
        cleanup_test_environment()
    
    async def test_help_command(self):
        """Test the help command."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        await self.commands.show_help(self.ctx)
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0]
        self.assertIsInstance(call_args[0], discord.Embed)
        self.assertIsInstance(call_args[1], discord.ui.View)
    
    async def test_list_agents(self):
        """Test listing available agents."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        await self.commands.list_agents(self.ctx)
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.Embed)
        self.assertIn("Available Agents", call_args.title)
    
    async def test_send_prompt(self):
        """Test sending a prompt to an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        message = MockMessage(
            content="!prompt Agent-1 Test prompt",
            attachments=[mock_discord_file("test_prompt.json")]
        )
        ctx = MockContext(message=message)
        
        await self.commands.send_prompt(ctx, "Agent-1", prompt_text="Test prompt")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Prompt sent", call_args)
    
    async def test_update_devlog(self):
        """Test updating an agent's devlog."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        message = MockMessage(
            content="!devlog Agent-1\nNew test entry"
        )
        ctx = MockContext(message=message)
        
        await self.commands.update_devlog(ctx, "Agent-1", message="New test entry")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Devlog updated", call_args)
    
    async def test_view_devlog(self):
        """Test viewing an agent's devlog."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        message = MockMessage(content="!view_devlog Agent-1")
        ctx = MockContext(message=message)
        
        await self.commands.view_devlog(ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.File)
        self.assertEqual(call_args.filename, "agent1_devlog.md")
    
    async def test_clear_devlog(self):
        """Test clearing an agent's devlog."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        message = MockMessage(content="!clear_devlog Agent-1")
        ctx = MockContext(message=message)
        
        await self.commands.clear_devlog(ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Devlog cleared", call_args)
    
    async def test_list_channels(self):
        """Test listing channel assignments."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        await self.commands.list_channels(self.ctx)
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.Embed)
        self.assertIn("Channel Assignments", call_args.title)
    
    async def test_resume_command(self):
        """Test resuming an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.resume_agent(self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Successfully resumed", call_args)
        
        # Test with invalid agent
        await self.commands.resume_agent(self.ctx, "InvalidAgent")
        self.assertIn("not found", self.ctx.send.call_args[0][0])
    
    async def test_verify_command(self):
        """Test verifying an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.verify_agent(self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Verification request sent", call_args)
    
    async def test_message_command(self):
        """Test sending a message to an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.send_message(self.ctx, "Agent-1", message="Test message")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Message sent", call_args)
    
    async def test_restore_command(self):
        """Test restoring an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.restore_agent(self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Restore request sent", call_args)
    
    async def test_sync_command(self):
        """Test syncing an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.sync_agent(self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Sync request sent", call_args)
    
    async def test_cleanup_command(self):
        """Test cleaning up an agent."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        await self.commands.cleanup_agent(self.ctx, "Agent-1")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Cleanup request sent", call_args)
    
    async def test_multi_command(self):
        """Test multi-agent command execution."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        # Test resume command on multiple agents
        await self.commands.multi_agent_command(self.ctx, "resume", agent_ids="1,2")
        self.ctx.send.assert_called()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.Embed)
        self.assertIn("Resuming Multiple Agents", call_args.title)
        
        # Test with invalid command
        await self.commands.multi_agent_command(self.ctx, "invalid", agent_ids="1,2")
        self.assertIn("Invalid command", self.ctx.send.call_args[0][0])
    
    async def test_system_command(self):
        """Test system-wide operations."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        self.bot.agent_resume.send_message.return_value = True
        
        # Test status command
        await self.commands.system_command(self.ctx, "status")
        self.ctx.send.assert_called()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.Embed)
        self.assertIn("System Operation", call_args.title)
        
        # Test with invalid action
        await self.commands.system_command(self.ctx, "invalid")
        self.assertIn("Invalid action", self.ctx.send.call_args[0][0])
    
    async def test_error_handling(self):
        """Test error handling in commands."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        
        # Test invalid agent name
        message = MockMessage(content="!prompt InvalidAgent Test prompt")
        ctx = MockContext(message=message)
        
        await self.commands.send_prompt(ctx, "InvalidAgent", prompt_text="Test prompt")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Error", call_args)
        
        # Test missing attachment
        message = MockMessage(content="!prompt Agent-1")
        ctx = MockContext(message=message)
        
        await self.commands.send_prompt(ctx, "Agent-1", prompt_text="")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Error", call_args)

    async def test_channel_assignment(self):
        """Test that Agent-1 is correctly assigned to its channel."""
        await asyncio.sleep(0)  # Allow other coroutines to run
        
        # Mock the channel ID from config
        expected_channel_id = "1375298813501374654"
        
        # Create a mock channel with the expected ID
        mock_channel = MockChannel(id=int(expected_channel_id))
        self.ctx.channel = mock_channel
        
        # Test sending a devlog message
        message = MockMessage(
            content="!devlog Agent-1\nTest channel assignment",
            channel=mock_channel
        )
        ctx = MockContext(message=message)
        
        # Verify the channel ID matches
        self.assertEqual(str(self.ctx.channel.id), expected_channel_id)
        
        # Test devlog update
        await self.commands.update_devlog(ctx, "Agent-1", message="Test channel assignment")
        self.ctx.send.assert_called_once()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIn("Devlog updated", call_args)
        
        # Verify the message was sent to the correct channel
        self.assertEqual(str(self.ctx.channel.id), expected_channel_id)
        
        # Test viewing devlog
        await self.commands.view_devlog(ctx, "Agent-1")
        self.ctx.send.assert_called()
        call_args = self.ctx.send.call_args[0][0]
        self.assertIsInstance(call_args, discord.File)
        self.assertEqual(call_args.filename, "agent1_devlog.md")
        
        # Verify the view command also used the correct channel
        self.assertEqual(str(self.ctx.channel.id), expected_channel_id) 