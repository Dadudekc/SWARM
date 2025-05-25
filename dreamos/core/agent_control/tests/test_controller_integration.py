"""
Integration tests for agent controller.

Tests the complete flow from controller actions to message delivery.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from ..controller import AgentController

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

def test_onboard_agent_flow(controller, tmp_runtime_dir):
    """Test complete onboarding flow."""
    agent_id = "Agent-1"
    controller.onboard_agent(agent_id)
    
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    assert agent_dir.exists()
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "ONBOARD"

def test_resume_agent_flow(controller, tmp_runtime_dir):
    """Test complete resume flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.resume_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "RESUME"

def test_verify_agent_flow(controller, tmp_runtime_dir):
    """Test complete verify flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.verify_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "VERIFY"

def test_repair_agent_flow(controller, tmp_runtime_dir):
    """Test complete repair flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.repair_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "REPAIR"

def test_backup_agent_flow(controller, tmp_runtime_dir):
    """Test complete backup flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.backup_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "BACKUP"

def test_restore_agent_flow(controller, tmp_runtime_dir):
    """Test complete restore flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.restore_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "RESTORE"

def test_send_message_flow(controller, tmp_runtime_dir):
    """Test complete message sending flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    message = "Test message"
    controller.send_message(agent_id, message)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["content"] == message

def test_cleanup_flow(controller, tmp_runtime_dir):
    """Test complete cleanup flow."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    controller.cleanup()
    
    assert controller.agent_operations.message_processor.cleanup.called
    assert controller.agent_operations.ui_automation.cleanup.called 