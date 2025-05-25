"""
Tests for the MenuBuilder's interaction with AgentController.
"""

import pytest
from unittest.mock import Mock, patch
from dreamos.core.agent_control.menu_builder import MenuBuilder
from dreamos.core.agent_control.controller import AgentController

@pytest.fixture
def mock_controller():
    """Create a mock controller with all required methods."""
    controller = Mock(spec=AgentController)
    controller.resume_agent = Mock()
    controller.verify_agent = Mock()
    controller.repair_agent = Mock()
    controller.backup_agent = Mock()
    controller.restore_agent = Mock()
    controller.send_message = Mock()
    controller.list_agents = Mock(return_value=["Agent-1", "Agent-2"])
    return controller

@pytest.fixture
def menu_builder(mock_controller):
    """Create a MenuBuilder instance with mock controller."""
    builder = MenuBuilder()
    builder.set_controller(mock_controller)
    return builder

def test_menu_action_triggers_controller(menu_builder, mock_controller):
    """Test that menu actions properly trigger controller methods."""
    # Test resume action
    menu_builder._handle_menu_action("resume", "Agent-1")
    mock_controller.resume_agent.assert_called_once_with("Agent-1")
    
    # Test verify action
    menu_builder._handle_menu_action("verify", "Agent-2")
    mock_controller.verify_agent.assert_called_once_with("Agent-2")
    
    # Test repair action
    menu_builder._handle_menu_action("repair", "Agent-1")
    mock_controller.repair_agent.assert_called_once_with("Agent-1")
    
    # Test backup action
    menu_builder._handle_menu_action("backup", "Agent-2")
    mock_controller.backup_agent.assert_called_once_with("Agent-2")
    
    # Test restore action
    menu_builder._handle_menu_action("restore", "Agent-1")
    mock_controller.restore_agent.assert_called_once_with("Agent-1")
    
    # Test message action
    menu_builder._handle_menu_action("message", "Agent-2")
    mock_controller.send_message.assert_called_once_with("Agent-2")

def test_menu_list_agents(menu_builder, mock_controller):
    """Test that listing agents updates the menu display."""
    # Setup mock menu
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    menu_builder.menu = mock_menu
    
    # Execute list action
    menu_builder._handle_menu_action("list", None)
    
    # Verify controller was called and status was updated
    mock_controller.list_agents.assert_called_once()
    mock_menu._status_panel.update_status.assert_called_once()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Agent-1" in status_call
    assert "Agent-2" in status_call

def test_menu_error_handling(menu_builder, mock_controller):
    """Test that menu errors are properly handled and displayed."""
    # Setup mock menu
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    menu_builder.menu = mock_menu
    
    # Make controller raise an error
    error_msg = "Test error"
    mock_controller.resume_agent.side_effect = Exception(error_msg)
    
    # Execute action that will fail
    menu_builder._handle_menu_action("resume", "Agent-1")
    
    # Verify error was displayed
    mock_menu._status_panel.update_status.assert_called_once()
    status_call = mock_menu._status_panel.update_status.call_args[0][0]
    assert "Error" in status_call
    assert error_msg in status_call

def test_menu_cleanup(menu_builder):
    """Test that menu cleanup properly disconnects signals."""
    # Setup mock menu
    mock_menu = Mock()
    menu_builder.menu = mock_menu
    
    # Execute cleanup
    menu_builder.cleanup()
    
    # Verify signals were disconnected
    mock_menu.disconnect_signals.assert_called_once()

def test_menu_builder_initialization():
    """Test MenuBuilder initialization and default state."""
    builder = MenuBuilder()
    assert builder.menu is None
    assert builder._controller is None

def test_menu_builder_set_controller():
    """Test setting controller on MenuBuilder."""
    builder = MenuBuilder()
    controller = Mock(spec=AgentController)
    
    builder.set_controller(controller)
    assert builder._controller == controller

def test_menu_builder_connect_signals(menu_builder):
    """Test that signals are properly connected when menu is built."""
    # Setup mock menu
    mock_menu = Mock()
    menu_builder.menu = mock_menu
    
    # Connect signals
    menu_builder.connect_signals(Mock())
    
    # Verify signals were connected
    mock_menu.connect_signals.assert_called_once()

def test_menu_builder_disconnect_signals(menu_builder):
    """Test that signals are properly disconnected."""
    # Setup mock menu
    mock_menu = Mock()
    menu_builder.menu = mock_menu
    
    # Disconnect signals
    menu_builder.disconnect_signals()
    
    # Verify signals were disconnected
    mock_menu.disconnect_signals.assert_called_once() 