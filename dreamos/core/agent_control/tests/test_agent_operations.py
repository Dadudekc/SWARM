"""
Unit tests for agent operations.

Tests the core functionality of agent operations.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

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
def agent_ops(tmp_runtime_dir):
    """Create an agent operations instance with temporary runtime directory."""
    ops = AgentOperations()
    ops.message_processor.base_path = tmp_runtime_dir
    ops.message_processor.mailbox_path = tmp_runtime_dir / "mailbox"
    return ops

def test_list_agents(agent_ops, tmp_runtime_dir):
    """Test listing available agents."""
    # Create some agent directories
    for i in range(3):
        agent_dir = tmp_runtime_dir / "mailbox" / f"Agent-{i}"
        agent_dir.mkdir()
    
    agents = agent_ops.list_agents()
    assert len(agents) == 3
    assert all(f"Agent-{i}" in agents for i in range(3))

def test_onboard_agent(agent_ops, tmp_runtime_dir):
    """Test onboarding a new agent."""
    agent_id = "Agent-1"
    agent_ops.onboard_agent(agent_id)
    
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    assert agent_dir.exists()
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "ONBOARD"

def test_resume_agent(agent_ops, tmp_runtime_dir):
    """Test resuming an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.resume_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "RESUME"

def test_verify_agent(agent_ops, tmp_runtime_dir):
    """Test verifying an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.verify_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "VERIFY"

def test_repair_agent(agent_ops, tmp_runtime_dir):
    """Test repairing an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.repair_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "REPAIR"

def test_backup_agent(agent_ops, tmp_runtime_dir):
    """Test backing up an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.backup_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "BACKUP"

def test_restore_agent(agent_ops, tmp_runtime_dir):
    """Test restoring an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.restore_agent(agent_id)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["mode"] == "RESTORE"

def test_send_message(agent_ops, tmp_runtime_dir):
    """Test sending a message to an agent."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    message = "Test message"
    agent_ops.send_message(agent_id, message)
    
    inbox = agent_dir / "inbox.json"
    assert inbox.exists()
    messages = json.loads(inbox.read_text())
    assert messages["content"] == message

def test_cleanup(agent_ops, tmp_runtime_dir):
    """Test cleaning up resources."""
    agent_id = "Agent-1"
    agent_dir = tmp_runtime_dir / "mailbox" / agent_id
    agent_dir.mkdir()
    
    agent_ops.cleanup()
    
    assert agent_ops.message_processor.cleanup.called
    assert agent_ops.ui_automation.cleanup.called 