"""
Integration tests for the complete agent control flow.
"""

import json
import pytest
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

def test_complete_resume_flow(controller, menu_builder, temp_runtime_dir):
    """Test the complete flow from menu action to resume message delivery."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Execute resume action through menu
    menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Verify status was updated
    mock_menu._status_panel.update_status.assert_called_with("Resuming Agent-1...")
    
    # Verify message was delivered
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["to_agent"] == "Agent-1"
        assert data["mode"] == "COMMAND"
        assert "resume" in data["content"].lower()

def test_complete_verify_flow(controller, menu_builder, temp_runtime_dir):
    """Test the complete flow from menu action to verify message delivery."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Execute verify action through menu
    menu_builder._handle_menu_action("verify", "Agent-1")
    
    # Verify status was updated
    mock_menu._status_panel.update_status.assert_called_with("Verifying Agent-1...")
    
    # Verify message was delivered
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["to_agent"] == "Agent-1"
        assert data["mode"] == "COMMAND"
        assert "verify" in data["content"].lower()

def test_complete_repair_flow(controller, menu_builder, temp_runtime_dir):
    """Test the complete flow from menu action to repair message delivery."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Execute repair action through menu
    menu_builder._handle_menu_action("repair", "Agent-1")
    
    # Verify status was updated
    mock_menu._status_panel.update_status.assert_called_with("Repairing Agent-1...")
    
    # Verify message was delivered
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["to_agent"] == "Agent-1"
        assert data["mode"] == "REPAIR"
        assert "repair" in data["content"].lower()

def test_complete_message_flow(controller, menu_builder, temp_runtime_dir):
    """Test the complete flow from menu action to custom message delivery."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Mock user input
    test_message = "Run diagnostics"
    with patch('builtins.input', return_value=test_message):
        # Execute message action through menu
        menu_builder._handle_menu_action("message", "Agent-1")
        
        # Verify status was updated
        mock_menu._status_panel.update_status.assert_called_with("Message sent to Agent-1")
        
        # Verify message was delivered
        inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
        assert inbox_path.exists()
        
        with inbox_path.open("r") as f:
            data = json.load(f)
            assert data["to_agent"] == "Agent-1"
            assert data["mode"] == "COMMAND"
            assert data["content"] == test_message

def test_error_propagation_flow(controller, menu_builder, temp_runtime_dir):
    """Test that errors properly propagate through the entire stack."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Make the inbox directory read-only to simulate IO error
    inbox_dir = temp_runtime_dir / "mailbox" / "Agent-1"
    inbox_dir.mkdir(parents=True)
    inbox_dir.chmod(0o444)  # Read-only
    
    # Execute resume action through menu
    menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Verify error was displayed in status panel
    mock_menu._status_panel.update_status.assert_called()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Error" in status_call

def test_concurrent_message_flow(controller, menu_builder, temp_runtime_dir):
    """Test handling multiple concurrent messages to different agents."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send messages to multiple agents
    agents = ["Agent-1", "Agent-2", "Agent-3"]
    for agent in agents:
        menu_builder._handle_menu_action("resume", agent)
    
    # Verify messages were delivered to all agents
    for agent in agents:
        inbox_path = temp_runtime_dir / "mailbox" / agent / "inbox.json"
        assert inbox_path.exists()
        
        with inbox_path.open("r") as f:
            data = json.load(f)
            assert data["to_agent"] == agent
            assert data["mode"] == "COMMAND"
            assert "resume" in data["content"].lower()

def test_cleanup_flow(controller, menu_builder, temp_runtime_dir):
    """Test the complete cleanup flow."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send some messages
    menu_builder._handle_menu_action("resume", "Agent-1")
    menu_builder._handle_menu_action("verify", "Agent-1")
    
    # Execute cleanup
    controller.cleanup()
    
    # Verify controller state
    assert not controller._running
    
    # Verify messages still exist (cleanup doesn't delete messages)
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-1" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 2  # Both messages should still be there

def test_menu_controller_binding(controller, menu_builder):
    """Test that menu and controller are properly bound together."""
    # Verify initial state
    assert menu_builder._controller == controller
    
    # Create new controller
    new_controller = AgentController()
    
    # Rebind menu to new controller
    menu_builder.set_controller(new_controller)
    
    # Verify rebinding
    assert menu_builder._controller == new_controller
    assert menu_builder._controller != controller 