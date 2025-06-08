"""Tests for task completion hooks."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_tools.autonomy.task_completion import (
    TaskCompletionHook,
    TaskCompletionManager,
    on_task_complete,
    TASK_TAGS
)

@pytest.fixture
def temp_config():
    """Create a temporary webhook config file."""
    config = {
        "Agent-1": {
            "webhook_url": "https://discord.com/api/webhooks/test1",
            "footer": "The Dream Architect | Agent-1"
        },
        "Agent-2": {
            "webhook_url": "https://discord.com/api/webhooks/test2",
            "footer": "The Memory Architect | Agent-2"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        json.dump(config, f)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_discord_devlog():
    """Create a mock DiscordDevlog instance."""
    mock = AsyncMock()
    mock.update_devlog.return_value = True
    return mock

@pytest.fixture
def task_completion_hook(mock_discord_devlog):
    """Create a TaskCompletionHook instance with mocked dependencies."""
    with patch('agent_tools.autonomy.task_completion.DiscordDevlog', return_value=mock_discord_devlog):
        hook = TaskCompletionHook(
            agent_id="Agent-1",
            webhook_url="https://discord.com/api/webhooks/test",
            footer="Test Footer"
        )
        yield hook

class TestTaskCompletionHook:
    """Test the TaskCompletionHook class."""
    
    def test_extract_mentioned_agents(self, task_completion_hook):
        """Test extraction of mentioned agents from content."""
        content = """
        Working with @Agent-2 on this feature.
        Also need input from @Agent-3.
        """
        
        mentioned = task_completion_hook._extract_mentioned_agents(content)
        assert mentioned == {"Agent-2", "Agent-3"}
    
    def test_generate_tags(self, task_completion_hook):
        """Test tag generation from task metadata."""
        task = {
            'title': 'Test Task',
            'status': 'done',
            'type': 'feature',
            'priority': 'high',
            'impact': 'major',
            'scope': 'core',
            'description': 'Working with @Agent-2 on this feature.'
        }
        
        tags = task_completion_hook._generate_tags(task)
        
        # Check agent source tag
        assert "#agent-1" in tags
        
        # Check status tag
        assert "#done" in tags
        
        # Check type tag
        assert "#feature" in tags
        
        # Check priority tag
        assert "#high" in tags
        
        # Check impact tag
        assert "#major" in tags
        
        # Check scope tag
        assert "#core" in tags
        
        # Check mentioned agent tag
        assert "#agent-2" in tags
        
        # Verify tags are sorted
        assert tags == sorted(tags)
    
    def test_format_task_summary(self, task_completion_hook):
        """Test formatting a task summary."""
        task = {
            'title': 'Test Task',
            'description': 'A test task description with @Agent-2',
            'task_id': 'TASK-123',
            'status': 'done',
            'type': 'feature',
            'priority': 'high',
            'impact': 'major',
            'scope': 'core'
        }
        
        summary = task_completion_hook._format_task_summary(task)
        
        # Check title
        assert "# Task Completed: Test Task" in summary
        
        # Check description
        assert "**Description:** A test task description" in summary
        
        # Check completion details
        assert "**Completed:**" in summary
        assert "**Task ID:** TASK-123" in summary
        
        # Check metadata section
        assert "**Status:** done" in summary
        assert "**Type:** feature" in summary
        assert "**Priority:** high" in summary
        assert "**Impact:** major" in summary
        assert "**Scope:** core" in summary
        
        # Check tags
        assert "#agent-1" in summary
        assert "#done" in summary
        assert "#feature" in summary
        assert "#high" in summary
        assert "#major" in summary
        assert "#core" in summary
        assert "#agent-2" in summary
    
    @pytest.mark.asyncio
    async def test_on_task_complete(self, task_completion_hook, tempfile):
        """Test task completion handling."""
        task = {
            'title': 'Test Task',
            'description': 'Working with @Agent-2',
            'task_id': 'TASK-123',
            'status': 'done',
            'type': 'feature'
        }
        
        # Mock the devlog file
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', tempfile.NamedTemporaryFile(mode='w')) as mock_file:
            
            success = await task_completion_hook.on_task_complete(task)
            
            assert success
            task_completion_hook.discord_devlog.update_devlog.assert_called_once()
            
            # Verify Discord update parameters
            call_args = task_completion_hook.discord_devlog.update_devlog.call_args[1]
            assert "Test Task" in call_args['title']
            assert "Working with @Agent-2" in call_args['content']
            assert call_args['memory_state']['status'] == 'done'
            assert call_args['memory_state']['type'] == 'feature'
            assert "Agent-2" in call_args['memory_state']['mentioned_agents']
    
    @pytest.mark.asyncio
    async def test_on_task_complete_failure(self, task_completion_hook):
        """Test task completion handling with Discord failure."""
        task = {'title': 'Test Task'}
        
        # Mock Discord failure
        task_completion_hook.discord_devlog.update_devlog.return_value = False
        
        success = await task_completion_hook.on_task_complete(task)
        assert not success

class TestTaskCompletionManager:
    """Test the TaskCompletionManager class."""
    
    def test_load_config(self, temp_config):
        """Test loading webhook configuration."""
        manager = TaskCompletionManager(config_path=temp_config)
        
        assert "Agent-1" in manager.hooks
        assert "Agent-2" in manager.hooks
        assert manager.hooks["Agent-1"].webhook_url == "https://discord.com/api/webhooks/test1"
        assert manager.hooks["Agent-2"].footer == "The Memory Architect | Agent-2"
    
    @pytest.mark.asyncio
    async def test_handle_task_completion(self, temp_config):
        """Test handling task completion for an agent."""
        manager = TaskCompletionManager(config_path=temp_config)
        
        task = {
            'title': 'Test Task',
            'status': 'done',
            'description': 'Working with @Agent-2'
        }
        
        success = await manager.handle_task_completion("Agent-1", task)
        assert success
        
        # Verify hook was called
        manager.hooks["Agent-1"].discord_devlog.update_devlog.assert_called_once()
        
        # Verify mentioned agents were tracked
        call_args = manager.hooks["Agent-1"].discord_devlog.update_devlog.call_args[1]
        assert "Agent-2" in call_args['memory_state']['mentioned_agents']
    
    @pytest.mark.asyncio
    async def test_handle_task_completion_unknown_agent(self, temp_config):
        """Test handling task completion for an unknown agent."""
        manager = TaskCompletionManager(config_path=temp_config)
        
        success = await manager.handle_task_completion("Unknown-Agent", {})
        assert not success

@pytest.mark.asyncio
async def test_global_on_task_complete(temp_config):
    """Test the global task completion handler."""
    task = {
        'title': 'Test Task',
        'status': 'done',
        'description': 'Working with @Agent-2'
    }
    
    success = await on_task_complete("Agent-1", task)
    assert success 
