"""
Integration tests for agent control system.

Tests complex integration scenarios and system-wide behaviors.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from dreamos.core.agent_control.controller import AgentController
from dreamos.core.agent_control.menu_builder import MenuBuilder

@pytest.fixture(autouse=True)
def mock_pyautogui():
    """Mock pyautogui functions for testing."""
    with patch('dreamos.core.agent_control.ui_automation.pyautogui.size', return_value=(1920, 1080)), \
         patch('dreamos.core.agent_control.ui_automation.pyautogui.moveTo'), \
         patch('dreamos.core.agent_control.ui_automation.pyautogui.click'), \
         patch('dreamos.core.agent_control.ui_automation.pyautogui.write'), \
         patch('dreamos.core.agent_control.ui_automation.pyautogui.hotkey'):
        yield

@pytest.fixture(autouse=True)
def mock_cellphone():
    """Mock CellPhone for testing."""
    with patch('dreamos.core.cell_phone.CellPhone.send_message') as mock_send:
        mock_send.return_value = True
        yield

@pytest.fixture
def temp_runtime_dir(tmp_path):
    """Create a temporary runtime directory structure."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    mailbox = runtime / "mailbox"
    mailbox.mkdir()
    return runtime

@pytest.fixture
def menu_builder():
    """Create a menu builder instance."""
    builder = MenuBuilder()
    # Mock the status panel update method
    builder.menu._status_panel.update_status = MagicMock()
    return builder

@pytest.fixture
def controller(temp_runtime_dir, menu_builder):
    """Create a controller instance with temporary runtime directory."""
    controller = AgentController()
    controller.menu_builder = menu_builder
    controller.agent_operations.message_processor.base_path = temp_runtime_dir
    controller.agent_operations.message_processor.mailbox_path = temp_runtime_dir / "mailbox"
    return controller

def test_error_propagation_flow(controller, menu_builder, temp_runtime_dir):
    """Test error propagation through the system."""
    agent_id = "Agent-1"
    agent_dir = temp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    # Simulate error in message processor
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = Exception("Test error")
        controller.resume_agent(agent_id)
    
    # Verify error was propagated to UI
    assert "Error resuming Agent-1: Test error" in menu_builder.menu._status_panel.update_status.call_args[0][0]

def test_concurrent_message_flow(controller, menu_builder, temp_runtime_dir):
    """Test handling of concurrent message operations."""
    agent_id = "Agent-1"
    agent_dir = temp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    # Simulate concurrent operations
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = BlockingIOError("Resource temporarily unavailable")
        controller.resume_agent(agent_id)
        controller.verify_agent(agent_id)
    
    # Verify system handled concurrent operations
    status_message = menu_builder.menu._status_panel.update_status.call_args[0][0]
    assert any(msg in status_message for msg in [
        "Error resuming Agent-1: Resource temporarily unavailable",
        "Error verifying Agent-1: Resource temporarily unavailable"
    ])

def test_system_cleanup_flow(controller, menu_builder, temp_runtime_dir):
    """Test system-wide cleanup process."""
    # Create multiple agent directories
    for i in range(3):
        agent_dir = temp_runtime_dir / "mailbox" / f"Agent-{i}"
        agent_dir.mkdir()
        inbox = agent_dir / "inbox.json"
        inbox.write_text(json.dumps({"content": "Test", "mode": "MESSAGE"}))
    
    # Mock cleanup methods
    controller.agent_operations.message_processor.cleanup = MagicMock()
    controller.agent_operations.ui_automation.cleanup = MagicMock()
    
    # Perform cleanup
    controller.cleanup()
    
    # Verify all resources were cleaned up
    assert controller.agent_operations.message_processor.cleanup.called
    assert controller.agent_operations.ui_automation.cleanup.called
    for i in range(3):
        inbox = temp_runtime_dir / "mailbox" / f"Agent-{i}" / "inbox.json"
        assert not inbox.exists() 