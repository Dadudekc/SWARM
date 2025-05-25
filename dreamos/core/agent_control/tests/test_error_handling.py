"""
Comprehensive error handling tests for agent control system.

Tests all error scenarios and recovery mechanisms.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

from ..controller import AgentController
from ..agent_operations import AgentOperations
from ...message_processor import MessageProcessor
from ...cell_phone import CellPhone

@pytest.fixture
def tmp_runtime_dir(tmp_path):
    """Create a temporary runtime directory structure."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    mailbox = runtime / "mailbox"
    mailbox.mkdir()
    return runtime

@pytest.fixture
def mock_menu_builder():
    """Create a mock menu builder."""
    builder = Mock()
    builder.menu = Mock()
    builder.menu._status_panel = Mock()
    return builder

@pytest.fixture
def controller(tmp_runtime_dir, mock_menu_builder):
    """Create a controller instance with temporary runtime directory."""
    controller = AgentController()
    controller.menu_builder = mock_menu_builder
    controller.agent_operations.message_processor.base_path = tmp_runtime_dir
    controller.agent_operations.message_processor.mailbox_path = tmp_runtime_dir / "mailbox"
    return controller

@pytest.fixture
def agent_ops(controller):
    """Get the agent operations instance from controller."""
    return controller.agent_operations

# Message Validation Tests
def test_handles_missing_message_mode(agent_ops):
    """Test handling of messages with missing mode."""
    with pytest.raises(ValueError, match="Missing mode"):
        agent_ops.message_processor.send_message("Agent-1", "Test", None)

def test_handles_missing_message_content(agent_ops):
    """Test handling of messages with missing content."""
    with pytest.raises(ValueError, match="Missing content"):
        agent_ops.message_processor.send_message("Agent-1", None, "RESUME")

# File System Tests
def test_handles_corrupt_inbox_file(controller, tmp_runtime_dir):
    """Test handling of corrupt inbox.json file."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    inbox = agent_dir / "inbox.json"
    inbox.write_text("invalid json content")
    
    controller.resume_agent("Agent-1")
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

def test_handles_missing_agent_directory(controller, tmp_runtime_dir):
    """Test handling of missing agent directory."""
    controller.resume_agent("NonExistentAgent")
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

def test_handles_permission_error(controller, tmp_runtime_dir):
    """Test handling of permission errors."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = PermissionError("Access denied")
        controller.resume_agent("Agent-1")
    
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

def test_handles_disk_full_error(controller, tmp_runtime_dir):
    """Test handling of disk full errors."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = OSError("No space left")
        controller.resume_agent("Agent-1")
    
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

# Network Tests
def test_handles_network_error(controller, tmp_runtime_dir):
    """Test handling of network errors."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = ConnectionError("Network unreachable")
        controller.resume_agent("Agent-1")
    
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

def test_handles_message_retry(controller, tmp_runtime_dir):
    """Test message retry mechanism."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = [
            ConnectionError("Temporary failure"),
            None  # Success on retry
        ]
        controller.resume_agent("Agent-1")
    
    assert mock_send.call_count == 2

# UI Tests
def test_handles_ui_timeout(controller, tmp_runtime_dir):
    """Test handling of UI automation timeouts."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.ui_automation, 'perform_onboarding_sequence') as mock_ui:
        mock_ui.side_effect = TimeoutError("UI operation timed out")
        controller.onboard_agent("Agent-1")
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()

def test_handles_ui_coordinate_error(controller, tmp_runtime_dir):
    """Test handling of invalid UI coordinates."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.ui_automation, 'perform_onboarding_sequence') as mock_ui:
        mock_ui.side_effect = ValueError("Invalid coordinates")
        controller.onboard_agent("Agent-1")
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()

# Queue Tests
def test_handles_queue_overflow(controller, tmp_runtime_dir):
    """Test handling of message queue overflow."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    queue_file = agent_dir / "queue.json"
    queue_file.write_text(json.dumps({"messages": ["msg"] * 1000}))
    
    controller.send_message("Agent-1")
    assert "Error sending message" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0]

# State Tests
def test_handles_state_transitions(controller, tmp_runtime_dir):
    """Test handling of agent state transitions."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    controller.verify_agent("Agent-1")
    controller.repair_agent("Agent-1")
    controller.resume_agent("Agent-1")
    
    inbox = agent_dir / "inbox.json"
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "RESUME"

def test_handles_concurrent_operations(controller, tmp_runtime_dir):
    """Test handling of concurrent operations."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    controller.resume_agent("Agent-1")
    controller.verify_agent("Agent-1")
    controller.repair_agent("Agent-1")
    
    inbox = agent_dir / "inbox.json"
    messages = json.loads(inbox.read_text())
    assert messages["mode"] in ["RESUME", "VERIFY", "REPAIR"]

# Cleanup Tests
def test_handles_cleanup_sequence(controller, tmp_runtime_dir):
    """Test handling of cleanup sequence."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.ui_automation, 'cleanup') as mock_cleanup:
        mock_cleanup.side_effect = Exception("UI cleanup failed")
        controller.cleanup()
    
    assert controller.agent_operations.message_processor.cleanup.called

# Fallback Tests
def test_handles_both_failures(controller, tmp_runtime_dir):
    """Test handling of both primary and fallback failures."""
    agent_dir = tmp_runtime_dir / "mailbox" / "Agent-1"
    agent_dir.mkdir()
    
    with patch.object(controller.agent_operations.message_processor, 'send_message') as mock_send:
        mock_send.side_effect = Exception("Processor failed")
        with patch.object(controller.agent_operations.cell_phone, 'send_message') as mock_cell:
            mock_cell.side_effect = Exception("Cell phone failed")
            controller.resume_agent("Agent-1")
    
    assert "Error resuming agent" in controller.menu_builder.menu._status_panel.update_status.call_args[0][0] 