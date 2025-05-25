"""
Tests for the MessageProcessor's message handling and delivery.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from dreamos.core.messaging import MessageProcessor, Message, MessageMode

@pytest.fixture
def temp_runtime_dir(tmp_path):
    """Create a temporary runtime directory structure."""
    runtime_dir = tmp_path / "runtime"
    mailbox_dir = runtime_dir / "mailbox"
    mailbox_dir.mkdir(parents=True)
    return runtime_dir

@pytest.fixture
def message_processor(temp_runtime_dir):
    """Create a MessageProcessor instance with temporary runtime directory."""
    return MessageProcessor(base_path=temp_runtime_dir)

def test_send_message_creates_inbox(message_processor, temp_runtime_dir):
    """Test that sending a message creates the agent's inbox."""
    # Create test message
    msg = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content="Test message",
        mode=MessageMode.COMMAND
    )
    
    # Send message
    message_processor.send_message(msg)
    
    # Verify inbox was created
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    # Verify message content
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["from_agent"] == "test_agent"
        assert data["to_agent"] == "Agent-1"
        assert data["content"] == "Test message"
        assert data["mode"] == "COMMAND"

def test_send_message_handles_existing_inbox(message_processor, temp_runtime_dir):
    """Test that sending a message appends to existing inbox."""
    # Create initial message
    msg1 = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content="First message",
        mode=MessageMode.COMMAND
    )
    message_processor.send_message(msg1)
    
    # Send second message
    msg2 = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content="Second message",
        mode=MessageMode.COMMAND
    )
    message_processor.send_message(msg2)
    
    # Verify both messages are in inbox
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["content"] == "First message"
        assert data[1]["content"] == "Second message"

def test_send_message_creates_agent_directory(message_processor, temp_runtime_dir):
    """Test that sending a message creates the agent's directory if it doesn't exist."""
    msg = Message(
        from_agent="test_agent",
        to_agent="New-Agent",
        content="Test message",
        mode=MessageMode.COMMAND
    )
    
    # Verify agent directory doesn't exist
    agent_dir = temp_runtime_dir / "mailbox" / "New-Agent"
    assert not agent_dir.exists()
    
    # Send message
    message_processor.send_message(msg)
    
    # Verify agent directory was created
    assert agent_dir.exists()
    assert agent_dir.is_dir()

def test_send_message_handles_invalid_message(message_processor):
    """Test that sending an invalid message raises appropriate error."""
    # Create invalid message (missing required fields)
    msg = Message(
        from_agent="test_agent",
        to_agent="",  # Invalid empty to_agent
        content="Test message",
        mode=MessageMode.COMMAND
    )
    
    # Verify sending invalid message raises error
    with pytest.raises(ValueError):
        message_processor.send_message(msg)

def test_send_message_handles_io_error(message_processor, temp_runtime_dir):
    """Test that IO errors during message sending are handled properly."""
    msg = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content="Test message",
        mode=MessageMode.COMMAND
    )
    
    # Make the inbox directory read-only to simulate IO error
    inbox_dir = temp_runtime_dir / "mailbox" / "Agent-1"
    inbox_dir.mkdir(parents=True)
    inbox_dir.chmod(0o444)  # Read-only
    
    # Verify sending message raises IO error
    with pytest.raises(IOError):
        message_processor.send_message(msg)

def test_message_mode_validation(message_processor):
    """Test that message modes are properly validated."""
    # Test valid modes
    valid_modes = [
        MessageMode.COMMAND,
        MessageMode.REPAIR,
        MessageMode.BACKUP,
        MessageMode.RESTORE
    ]
    
    for mode in valid_modes:
        msg = Message(
            from_agent="test_agent",
            to_agent="Agent-1",
            content="Test message",
            mode=mode
        )
        # Should not raise any error
        message_processor.send_message(msg)
    
    # Test invalid mode
    with pytest.raises(ValueError):
        msg = Message(
            from_agent="test_agent",
            to_agent="Agent-1",
            content="Test message",
            mode="INVALID_MODE"  # Invalid mode
        )
        message_processor.send_message(msg)

def test_message_cleanup(message_processor, temp_runtime_dir):
    """Test that message cleanup properly removes old messages."""
    # Send some messages
    for i in range(3):
        msg = Message(
            from_agent="test_agent",
            to_agent="Agent-1",
            content=f"Message {i}",
            mode=MessageMode.COMMAND
        )
        message_processor.send_message(msg)
    
    # Clean up messages older than 1 second
    message_processor.cleanup_messages(max_age_seconds=1)
    
    # Verify messages were cleaned up
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 0 