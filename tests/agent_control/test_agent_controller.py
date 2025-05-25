"""
Tests for the AgentController messaging system integration.
"""

import pytest
from unittest.mock import Mock, patch
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.messaging import MessageProcessor
from dreamos.core import CellPhone
from dreamos.core.agent_control.agent_operations import AgentOperations

@pytest.fixture
def controller():
    """Create a test controller instance."""
    return AgentController()

@pytest.fixture
def mock_menu():
    """Create a mock menu with status panel."""
    menu = Mock()
    menu._status_panel = Mock()
    menu._status_panel.update_status = Mock()
    return menu

def test_controller_initialization(controller):
    """Test controller initialization with messaging components."""
    assert isinstance(controller.message_processor, MessageProcessor)
    assert isinstance(controller.cell_phone, CellPhone)
    assert isinstance(controller.agent_operations, AgentOperations)

def test_resume_agent(controller, mock_menu):
    """Test resume agent operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    
    # Mock agent operations
    with patch.object(controller.agent_operations, 'resume_agent') as mock_resume:
        # Execute
        controller.resume_agent(agent_id)
        
        # Verify
        mock_resume.assert_called_once_with(agent_id)
        mock_menu._status_panel.update_status.assert_called_with(f"Resuming {agent_id}...")

def test_verify_agent(controller, mock_menu):
    """Test verify agent operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    
    # Mock agent operations
    with patch.object(controller.agent_operations, 'verify_agent') as mock_verify:
        # Execute
        controller.verify_agent(agent_id)
        
        # Verify
        mock_verify.assert_called_once_with(agent_id)
        mock_menu._status_panel.update_status.assert_called_with(f"Verifying {agent_id}...")

def test_repair_agent(controller, mock_menu):
    """Test repair agent operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    
    # Mock agent operations
    with patch.object(controller.agent_operations, 'repair_agent') as mock_repair:
        # Execute
        controller.repair_agent(agent_id)
        
        # Verify
        mock_repair.assert_called_once_with(agent_id)
        mock_menu._status_panel.update_status.assert_called_with(f"Repairing {agent_id}...")

def test_backup_agent(controller, mock_menu):
    """Test backup agent operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    
    # Mock agent operations
    with patch.object(controller.agent_operations, 'backup_agent') as mock_backup:
        # Execute
        controller.backup_agent(agent_id)
        
        # Verify
        mock_backup.assert_called_once_with(agent_id)
        mock_menu._status_panel.update_status.assert_called_with(f"Backing up {agent_id}...")

def test_restore_agent(controller, mock_menu):
    """Test restore agent operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    
    # Mock agent operations
    with patch.object(controller.agent_operations, 'restore_agent') as mock_restore:
        # Execute
        controller.restore_agent(agent_id)
        
        # Verify
        mock_restore.assert_called_once_with(agent_id)
        mock_menu._status_panel.update_status.assert_called_with(f"Restoring {agent_id}...")

def test_send_message(controller, mock_menu):
    """Test send message operation."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    test_message = "Test message"
    
    # Mock input and agent operations
    with patch('builtins.input', return_value=test_message), \
         patch.object(controller.agent_operations, 'send_message') as mock_send:
        # Execute
        controller.send_message(agent_id)
        
        # Verify
        mock_send.assert_called_once_with(agent_id, test_message)
        mock_menu._status_panel.update_status.assert_called_with(f"Message sent to {agent_id}")

def test_error_handling(controller, mock_menu):
    """Test error handling in agent operations."""
    # Setup
    controller.menu_builder = Mock()
    controller.menu_builder.menu = mock_menu
    agent_id = "test_agent"
    error_message = "Test error"
    
    # Mock agent operations to raise an error
    with patch.object(controller.agent_operations, 'resume_agent', 
                     side_effect=Exception(error_message)):
        # Execute
        controller.resume_agent(agent_id)
        
        # Verify error handling
        mock_menu._status_panel.update_status.assert_called_with(
            f"Error resuming {agent_id}: {error_message}"
        )

def test_menu_action_handling(controller):
    """Test menu action handling."""
    # Setup
    test_agent = "test_agent"
    test_action = "resume"
    
    # Mock agent operations
    with patch.object(controller, 'resume_agent') as mock_resume:
        # Execute
        controller._handle_menu_action(test_action, test_agent)
        
        # Verify
        mock_resume.assert_called_once_with(test_agent)

def test_cleanup(controller):
    """Test controller cleanup."""
    # Setup
    controller.menu_builder = Mock()
    controller.agent_operations = Mock()
    controller.ui_automation = Mock()
    
    # Execute
    controller.cleanup()
    
    # Verify
    assert not controller._running
    controller.menu_builder.disconnect_signals.assert_called_once()
    controller.agent_operations.cleanup.assert_called_once()
    controller.ui_automation.cleanup.assert_called_once() 