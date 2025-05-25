"""
Edge case tests for the agent control system.
"""

import json
import os
import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.agent_control.menu_builder import MenuBuilder
from dreamos.core.messaging import MessageProcessor, Message, MessageMode
from dreamos.core.agent_control.agent_operations import AgentOperations

@pytest.fixture
def temp_runtime_dir(tmp_path):
    """Create a temporary runtime directory structure."""
    runtime_dir = tmp_path / "runtime"
    mailbox_dir = runtime_dir / "mailbox"
    mailbox_dir.mkdir(parents=True)
    return runtime_dir

@pytest.fixture
def message_processor(temp_runtime_dir):
    """Create a real MessageProcessor instance."""
    return MessageProcessor(base_path=temp_runtime_dir)

@pytest.fixture
def agent_operations(message_processor):
    """Create a real AgentOperations instance."""
    return AgentOperations()

@pytest.fixture
def controller(message_processor, agent_operations):
    """Create a real AgentController instance."""
    controller = AgentController()
    controller.message_processor = message_processor
    controller.agent_operations = agent_operations
    return controller

@pytest.fixture
def menu_builder(controller):
    """Create a real MenuBuilder instance."""
    builder = MenuBuilder()
    builder.set_controller(controller)
    return builder

def test_missing_inbox_directory(controller, menu_builder, temp_runtime_dir):
    """Test system behavior when inbox directory is missing."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Remove mailbox directory
    mailbox_dir = temp_runtime_dir / "mailbox"
    shutil.rmtree(mailbox_dir)
    
    # Execute resume action through menu
    menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Verify system created directory and delivered message
    assert mailbox_dir.exists()
    inbox_path = mailbox_dir / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["to_agent"] == "Agent-1"
        assert data["mode"] == "COMMAND"

def test_agent_error_state_recovery(controller, menu_builder, temp_runtime_dir):
    """Test system behavior when agent is in error state."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create error state file
    agent_dir = temp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir(parents=True)
    error_file = agent_dir / "error_state.json"
    with error_file.open("w") as f:
        json.dump({"error": "Test error", "timestamp": "2024-01-01T00:00:00Z"}, f)
    
    # Execute repair action through menu
    menu_builder._handle_menu_action("repair", "Agent-1")
    
    # Verify repair message was sent
    inbox_path = agent_dir / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["mode"] == "REPAIR"
        assert "repair" in data["content"].lower()
    
    # Verify error state was cleared
    assert not error_file.exists()

def test_invalid_message_mode(controller, menu_builder, temp_runtime_dir):
    """Test system behavior with invalid message mode."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create message with invalid mode
    msg = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content="Test message",
        mode="INVALID_MODE"
    )
    
    # Verify sending invalid message raises error
    with pytest.raises(ValueError):
        controller.message_processor.send_message(msg)
    
    # Verify error was displayed in status panel
    mock_menu._status_panel.update_status.assert_called()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Error" in status_call

def test_malformed_message_content(controller, menu_builder, temp_runtime_dir):
    """Test system behavior with malformed message content."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create message with malformed content
    msg = Message(
        from_agent="test_agent",
        to_agent="Agent-1",
        content=None,  # Invalid content
        mode=MessageMode.COMMAND
    )
    
    # Verify sending malformed message raises error
    with pytest.raises(ValueError):
        controller.message_processor.send_message(msg)

def test_concurrent_inbox_access(controller, menu_builder, temp_runtime_dir):
    """Test system behavior with concurrent inbox access."""
    import threading
    import time
    
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create multiple threads sending messages
    def send_message():
        menu_builder._handle_menu_action("resume", "Agent-1")
    
    threads = [threading.Thread(target=send_message) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Verify all messages were delivered
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 5  # All messages should be present

def test_invalid_agent_id(controller, menu_builder, temp_runtime_dir):
    """Test system behavior with invalid agent ID."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Execute action with invalid agent ID
    menu_builder._handle_menu_action("resume", "")
    
    # Verify error was displayed
    mock_menu._status_panel.update_status.assert_called()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Error" in status_call
    assert "Invalid agent ID" in status_call

def test_message_cleanup_edge_cases(controller, menu_builder, temp_runtime_dir):
    """Test message cleanup behavior with edge cases."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create some messages
    menu_builder._handle_menu_action("resume", "Agent-1")
    menu_builder._handle_menu_action("verify", "Agent-1")
    
    # Make inbox read-only
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    os.chmod(inbox_path, 0o444)
    
    # Verify cleanup handles read-only file gracefully
    controller.message_processor.cleanup_messages(max_age_seconds=0)
    
    # Verify messages still exist
    assert inbox_path.exists()
    
    # Restore permissions
    os.chmod(inbox_path, 0o644)

def test_agent_directory_permissions(controller, menu_builder, temp_runtime_dir):
    """Test system behavior with various directory permissions."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create agent directory with restrictive permissions
    agent_dir = temp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir(parents=True)
    os.chmod(agent_dir, 0o444)  # Read-only
    
    # Execute action
    menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Verify error was displayed
    mock_menu._status_panel.update_status.assert_called()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Error" in status_call
    
    # Restore permissions
    os.chmod(agent_dir, 0o755)

def test_message_ordering(controller, menu_builder, temp_runtime_dir):
    """Test that messages maintain proper ordering."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send multiple messages
    actions = ["resume", "verify", "repair"]
    for action in actions:
        menu_builder._handle_menu_action(action, "Agent-1")
    
    # Verify messages are in correct order
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 3
        assert "resume" in data[0]["content"].lower()
        assert "verify" in data[1]["content"].lower()
        assert "repair" in data[2]["content"].lower() 