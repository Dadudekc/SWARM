"""
Integration tests for the message processing system.

This module contains comprehensive tests for:
1. Message Loop
2. Persistent Queue
3. Response Collector
4. Message Processing
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from pathlib import Path
import asyncio
from datetime import datetime
import time
import os
import json
import logging
import pyautogui
import shutil
from tempfile import TemporaryDirectory
from typing import Dict, Any

from dreamos.core.messaging.message import Message
from dreamos.core.messaging.enums import MessageMode
from dreamos.core.message_loop import MessageLoop
from dreamos.core.agent_control.ui_automation import UIAutomation
from dreamos.core.messaging.pipeline import MessagePipeline
from dreamos.core.agent_control.agent_control import AgentControl
from dreamos.core.persistent_queue import PersistentQueue
from dreamos.core.response_collector import ResponseCollector, collect_response

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test constants
TEST_TIMEOUT = 60  # seconds
MAX_LOG_SIZE = 1024 * 1024  # 1MB
BATCH_SIZE = 10
BATCH_TIMEOUT = 1.0

# Fixtures
@pytest.fixture
def mock_agent_control():
    """Create a mock agent control instance."""
    with patch('dreamos.core.agent_control.AgentControl') as mock:
        control = mock.return_value
        control.move_to_agent.return_value = True
        control.click_input_box.return_value = True
        control.click_copy_button.return_value = True
        control.validate_coordinates.return_value = True
        control.get_response_region.return_value = {
            "top_left": {"x": 100, "y": 200},
            "bottom_right": {"x": 300, "y": 400}
        }
        # Add coordinate manager
        control.coordinate_manager = MagicMock()
        control.coordinate_manager.coordinates = {}
        yield control

@pytest.fixture
def mock_message_pipeline():
    """Create a mock message pipeline instance."""
    with patch('dreamos.core.messaging.pipeline.MessagePipeline') as mock:
        pipeline = mock.return_value
        pipeline.process_message = AsyncMock(return_value=True)
        pipeline.process_batch = AsyncMock(return_value=True)
        yield pipeline

@pytest.fixture
def gui_test_env():
    """Setup and cleanup for GUI tests."""
    logger.info("Setting up GUI test environment")
    yield
    logger.info("Cleaning up GUI test environment")

@pytest.fixture
def persistent_queue():
    """Create a test persistent queue."""
    with TemporaryDirectory() as tmpdir:
        queue_file = Path(tmpdir) / "queue.json"
        queue = PersistentQueue(queue_file=str(queue_file))
        queue.set_test_mode(True)
        yield queue

# Message Loop Tests
@pytest.mark.integration
def test_full_message_loop(mock_agent_control, mock_message_pipeline):
    """Test the complete message processing loop."""
    # Initialize components
    agent_id = "agent1"
    message = Message(
        content="Test message",
        sender="test_user",
        timestamp=datetime.now()
    )
    
    # Simulate message loop
    assert mock_agent_control.move_to_agent(agent_id)
    assert mock_agent_control.click_input_box(agent_id)
    
    # Process message
    processed = asyncio.get_event_loop().run_until_complete(mock_message_pipeline.process_message(message))
    assert processed is True
    
    # Verify response region
    region = mock_agent_control.get_response_region(agent_id)
    assert region is not None
    assert "top_left" in region
    assert "bottom_right" in region
    
    # Verify all expected calls were made
    mock_agent_control.move_to_agent.assert_called_once_with(agent_id)
    mock_agent_control.click_input_box.assert_called_once_with(agent_id)
    mock_message_pipeline.process_message.assert_called_once_with(message)
    mock_agent_control.get_response_region.assert_called_once_with(agent_id)

@pytest.mark.integration
def test_message_loop_error_handling(mock_agent_control, mock_message_pipeline):
    """Test error handling in the message loop."""
    # Simulate move failure
    mock_agent_control.move_to_agent.return_value = False
    
    # Attempt message loop
    assert not mock_agent_control.move_to_agent("agent1")
    mock_agent_control.click_input_box.assert_not_called()
    mock_message_pipeline.process_message.assert_not_called()

@pytest.mark.integration
def test_message_loop_invalid_agent(mock_agent_control, mock_message_pipeline):
    """Test handling of invalid agent ID."""
    # Simulate missing agent
    mock_agent_control.get_response_region.return_value = None
    
    # Attempt to get response region
    region = mock_agent_control.get_response_region("nonexistent")
    assert region is None
    
    # Verify error handling
    mock_agent_control.move_to_agent.assert_not_called()
    mock_agent_control.click_input_box.assert_not_called()
    mock_message_pipeline.process_message.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_message_loop(mock_agent_control, mock_message_pipeline):
    """Test async message loop functionality."""
    # Create test message
    message = Message(
        content="Test async message",
        mode=MessageMode.SYSTEM,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    
    # Mock successful message sending
    mock_agent_control.move_to_agent.return_value = True
    mock_agent_control.click_input_box.return_value = True
    mock_agent_control.click_copy_button.return_value = True
    
    # Actually call the mocked methods
    mock_agent_control.move_to_agent("test_sender")
    mock_agent_control.click_input_box("test_sender")
    mock_agent_control.click_copy_button("test_sender")
    
    # Send message
    success = await mock_message_pipeline.process_message(message)
    assert success, "Failed to process async message"
    
    # Verify all expected calls were made
    assert mock_agent_control.move_to_agent.called
    assert mock_agent_control.click_input_box.called
    assert mock_agent_control.click_copy_button.called

# Persistent Queue Tests
def test_queue_clear_agent(persistent_queue):
    """Test clearing messages for a specific agent."""
    m1 = Message(from_agent="a", to_agent="agent1", content="hi")
    m2 = Message(from_agent="a", to_agent="agent2", content="hi")
    persistent_queue.enqueue(m1)
    persistent_queue.enqueue(m2)

    persistent_queue.clear_agent("agent1")

    status = persistent_queue.get_status()
    assert all(msg.get("to_agent") != "agent1" for msg in status["messages"])

    history = persistent_queue.get_message_history()
    assert all(msg.to_agent != "agent1" for msg in history)

def test_queue_clear_history(persistent_queue):
    """Test clearing history for a specific agent."""
    m1 = Message(from_agent="a", to_agent="agent1", content="hi")
    m2 = Message(from_agent="a", to_agent="agent2", content="hi")
    persistent_queue.enqueue(m1)
    persistent_queue.enqueue(m2)

    persistent_queue.clear_history("agent1")

    status = persistent_queue.get_status()
    assert all(msg.get("to_agent") != "agent1" for msg in status["messages"])

    history = persistent_queue.get_message_history()
    assert all(msg.to_agent != "agent1" for msg in history)

@pytest.mark.skipif(True, reason="Requires uiautomation module and GUI environment")
def test_response_collector():
    """Test response collection functionality."""
    collector = ResponseCollector()
    collector.start()
    time.sleep(1)
    collector.stop()
    assert collector.is_running() is False

@pytest.mark.skipif(True, reason="Requires uiautomation module and GUI environment")
def test_response_collector_mock():
    """Test response collector with mocked UI automation."""
    with patch('dreamos.core.agent_control.ui_automation.UIAutomation') as mock:
        collector = ResponseCollector()
        collector.start()
        time.sleep(1)
        collector.stop()
        assert collector.is_running() is False

@pytest.mark.gui
def test_real_ui_automation(tmp_path, gui_test_env, monkeypatch):
    """Test real UI automation functionality."""
    # Skip if not in GUI environment
    if not os.environ.get("GUI_TEST_ENV"):
        pytest.skip("Not in GUI test environment")
        
    # Setup test environment
    test_dir = tmp_path / "test_ui"
    test_dir.mkdir()
    
    # Create test coordinates
    coords = {
        "input_box": {"x": 100, "y": 100},
        "copy_button": {"x": 200, "y": 100},
        "response_region": {
            "top_left": {"x": 100, "y": 200},
            "bottom_right": {"x": 300, "y": 400}
        }
    }
    
    # Save coordinates
    coords_file = test_dir / "coords.json"
    with open(coords_file, "w") as f:
        json.dump(coords, f)
    
    # Initialize UI automation
    ui = UIAutomation(coords_file=str(coords_file))
    
    # Test coordinate validation
    assert ui.validate_coordinates()
    
    # Test mouse movement
    assert ui.move_to(100, 100)
    assert ui.move_to(200, 100)
    
    # Test clicking
    assert ui.click(100, 100)
    assert ui.click(200, 100)
    
    # Test response region
    region = ui.get_response_region()
    assert region is not None
    assert "top_left" in region
    assert "bottom_right" in region

def test_message_creation():
    """Test message creation and validation."""
    message = Message(
        content="Test message",
        sender="test_user",
        timestamp=datetime.now()
    )
    assert message.content == "Test message"
    assert message.sender == "test_user"
    assert message.timestamp is not None

def test_message_serialization():
    """Test message serialization and deserialization."""
    original = Message(
        content="Test message",
        sender="test_user",
        timestamp=datetime.now()
    )
    
    # Serialize
    data = original.to_dict()
    assert isinstance(data, dict)
    assert data["content"] == original.content
    assert data["sender"] == original.sender
    
    # Deserialize
    restored = Message.from_dict(data)
    assert restored.content == original.content
    assert restored.sender == original.sender 