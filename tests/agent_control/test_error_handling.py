"""
Tests for error handling and escalation in the agent control system.
"""

import pytest
from unittest.mock import Mock, patch
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.messaging import MessageProcessor, Message, MessageMode

@pytest.fixture
def mock_menu():
    """Create a mock menu with status panel."""
    menu = Mock()
    menu._status_panel = Mock()
    menu._status_panel.update_status = Mock()
    return menu

@pytest.fixture
def controller_with_menu(mock_menu):
    """Create a controller with mock menu."""
    controller = AgentController()
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    return controller

def test_controller_handles_message_send_failure(controller_with_menu, mock_menu):
    """Test that controller handles message send failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to send message"
    with patch.object(controller_with_menu.agent_operations, 'send_message',
                     side_effect=Exception(error_msg)):
        # Execute send_message
        controller_with_menu.send_message("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error sending message to Agent-1: {error_msg}"
        )

def test_controller_handles_resume_failure(controller_with_menu, mock_menu):
    """Test that controller handles resume operation failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to resume agent"
    with patch.object(controller_with_menu.agent_operations, 'resume_agent',
                     side_effect=Exception(error_msg)):
        # Execute resume_agent
        controller_with_menu.resume_agent("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error resuming Agent-1: {error_msg}"
        )

def test_controller_handles_verify_failure(controller_with_menu, mock_menu):
    """Test that controller handles verify operation failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to verify agent"
    with patch.object(controller_with_menu.agent_operations, 'verify_agent',
                     side_effect=Exception(error_msg)):
        # Execute verify_agent
        controller_with_menu.verify_agent("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error verifying Agent-1: {error_msg}"
        )

def test_controller_handles_repair_failure(controller_with_menu, mock_menu):
    """Test that controller handles repair operation failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to repair agent"
    with patch.object(controller_with_menu.agent_operations, 'repair_agent',
                     side_effect=Exception(error_msg)):
        # Execute repair_agent
        controller_with_menu.repair_agent("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error repairing Agent-1: {error_msg}"
        )

def test_controller_handles_backup_failure(controller_with_menu, mock_menu):
    """Test that controller handles backup operation failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to backup agent"
    with patch.object(controller_with_menu.agent_operations, 'backup_agent',
                     side_effect=Exception(error_msg)):
        # Execute backup_agent
        controller_with_menu.backup_agent("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error backing up Agent-1: {error_msg}"
        )

def test_controller_handles_restore_failure(controller_with_menu, mock_menu):
    """Test that controller handles restore operation failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to restore agent"
    with patch.object(controller_with_menu.agent_operations, 'restore_agent',
                     side_effect=Exception(error_msg)):
        # Execute restore_agent
        controller_with_menu.restore_agent("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error restoring Agent-1: {error_msg}"
        )

def test_controller_handles_menu_action_failure(controller_with_menu, mock_menu):
    """Test that controller handles menu action failures."""
    # Setup mock agent operations to raise an error
    error_msg = "Failed to execute menu action"
    with patch.object(controller_with_menu, 'resume_agent',
                     side_effect=Exception(error_msg)):
        # Execute menu action
        controller_with_menu._handle_menu_action("resume", "Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error: {error_msg}"
        )

def test_controller_handles_cleanup_failure(controller_with_menu):
    """Test that controller handles cleanup failures gracefully."""
    # Setup mocks to raise errors during cleanup
    controller_with_menu.menu_builder.disconnect_signals.side_effect = Exception("Menu cleanup failed")
    controller_with_menu.agent_operations.cleanup.side_effect = Exception("Operations cleanup failed")
    controller_with_menu.ui_automation.cleanup.side_effect = Exception("UI cleanup failed")
    
    # Execute cleanup
    controller_with_menu.cleanup()
    
    # Verify controller state is still cleaned up
    assert not controller_with_menu._running

def test_controller_handles_invalid_agent_id(controller_with_menu, mock_menu):
    """Test that controller handles invalid agent IDs."""
    # Execute with invalid agent ID
    controller_with_menu.resume_agent("")
    
    # Verify error was displayed
    mock_menu._status_panel.update_status.assert_called_with(
        "Error resuming : Invalid agent ID"
    )

def test_controller_handles_message_processor_failure(controller_with_menu, mock_menu):
    """Test that controller handles message processor failures."""
    # Setup message processor to raise an error
    error_msg = "Message processor error"
    with patch.object(controller_with_menu.message_processor, 'send_message',
                     side_effect=Exception(error_msg)):
        # Execute send_message
        controller_with_menu.send_message("Agent-1")
        
        # Verify error was displayed
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error sending message to Agent-1: {error_msg}"
        ) 