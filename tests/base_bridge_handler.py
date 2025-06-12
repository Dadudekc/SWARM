"""Tests for the base_bridge_handler module."""

import asyncio
import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from watchdog.events import FileCreatedEvent, FileModifiedEvent

from dreamos.core.autonomy.handlers.bridge.base_bridge_handler import BaseBridgeHandler

# Test implementation of BaseBridgeHandler
class TestBridgeHandler(BaseBridgeHandler):
    """Test implementation of BaseBridgeHandler."""
    
    async def _process_file(self, file_path: str) -> bool:
        """Test implementation of _process_file."""
        return True

@pytest.fixture
def sample_config():
    """Fixture for sample configuration."""
    return {
        "watch_dir": "test_watch_dir",
        "file_pattern": "*.json"
    }

@pytest.fixture
def watch_dir(tmp_path):
    """Fixture for watch directory."""
    return tmp_path

@pytest.fixture
def mock_agent_loop():
    """Fixture for mock agent loop."""
    return AsyncMock()

@pytest.fixture
async def handler(watch_dir, sample_config, mock_agent_loop):
    """Fixture for test handler instance."""
    handler = TestBridgeHandler(sample_config, watch_dir, mock_agent_loop)
    return handler

@pytest.mark.asyncio
async def test_init(handler, watch_dir, sample_config):
    """Test initialization of BaseBridgeHandler."""
    assert handler.watch_dir == watch_dir
    assert handler.file_pattern == sample_config["file_pattern"]

@pytest.mark.asyncio
async def test_on_created_triggers_process_file(handler, watch_dir):
    """Test that on_created triggers _process_file."""
    # Create a test file
    test_file = watch_dir / "test.json"
    test_file.write_text(json.dumps({"test": "data"}))
    
    # Mock _process_file
    mock_process = AsyncMock(return_value=True)
    with patch.object(TestBridgeHandler, '_process_file', mock_process):
        # Create event
        event = FileCreatedEvent(str(test_file))
        
        # Mock create_task to run synchronously
        async def mock_create_task(coro):
            return await coro
            
        with patch('asyncio.create_task', mock_create_task):
            # Call on_created
            handler.on_created(event)
            
            # Allow async tasks to queue up
            await asyncio.sleep(0.1)
            
            # Verify _process_file was called
            mock_process.assert_called_once_with(str(test_file))

@pytest.mark.asyncio
async def test_on_modified_triggers_process_file(handler, watch_dir):
    """Test that on_modified triggers _process_file."""
    # Create a test file
    test_file = watch_dir / "test.json"
    test_file.write_text(json.dumps({"test": "data"}))
    
    # Mock _process_file
    mock_process = AsyncMock(return_value=True)
    with patch.object(TestBridgeHandler, '_process_file', mock_process):
        # Create event
        event = FileModifiedEvent(str(test_file))
        
        # Mock create_task to run synchronously
        async def mock_create_task(coro):
            return await coro
            
        with patch('asyncio.create_task', mock_create_task):
            # Call on_modified
            handler.on_modified(event)
            
            # Allow async tasks to queue up
            await asyncio.sleep(0.1)
            
            # Verify _process_file was called
            mock_process.assert_called_once_with(str(test_file))
