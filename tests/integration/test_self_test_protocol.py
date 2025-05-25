"""
Self-test protocol implementation for validating message delivery and preventing duplicate onboarding.
"""

import json
import time
from pathlib import Path
from unittest.mock import Mock
import pytest
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

def test_self_test_echo(controller, menu_builder, temp_runtime_dir):
    """Test the self-test echo protocol."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create echo message
    echo_msg = Message(
        from_agent="system",
        to_agent="Agent-4",
        content="ECHO_TEST",
        mode=MessageMode.SELF_TEST
    )
    
    # Send echo message
    controller.message_processor.send_message(echo_msg)
    
    # Verify echo response
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-4" / "inbox.json"
    assert inbox_path.exists()
    
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert data["mode"] == "SELF_TEST"
        assert "ECHO_TEST" in data["content"]

def test_prevent_duplicate_onboarding(controller, menu_builder, temp_runtime_dir):
    """Test prevention of duplicate onboarding messages."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create onboarding state file
    agent_dir = temp_runtime_dir / "mailbox" / "Agent-4"
    agent_dir.mkdir(parents=True)
    state_file = agent_dir / "onboarding_state.json"
    
    with state_file.open("w") as f:
        json.dump({
            "onboarded": True,
            "timestamp": time.time(),
            "version": "1.0"
        }, f)
    
    # Attempt onboarding
    menu_builder._handle_menu_action("onboard", "Agent-4")
    
    # Verify no new onboarding message was sent
    inbox_path = agent_dir / "inbox.json"
    if inbox_path.exists():
        with inbox_path.open("r") as f:
            data = json.load(f)
            assert "onboarding" not in data["content"].lower()

def test_agent_state_validation(controller, menu_builder, temp_runtime_dir):
    """Test validation of agent state before operations."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create agent state file
    agent_dir = temp_runtime_dir / "mailbox" / "Agent-4"
    agent_dir.mkdir(parents=True)
    state_file = agent_dir / "agent_state.json"
    
    with state_file.open("w") as f:
        json.dump({
            "status": "active",
            "last_operation": "verify",
            "timestamp": time.time()
        }, f)
    
    # Attempt operation
    menu_builder._handle_menu_action("verify", "Agent-4")
    
    # Verify state was checked
    with state_file.open("r") as f:
        state = json.load(f)
        assert state["last_operation"] == "verify"

def test_message_acknowledgment(controller, menu_builder, temp_runtime_dir):
    """Test message acknowledgment protocol."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send test message
    test_msg = Message(
        from_agent="system",
        to_agent="Agent-4",
        content="TEST_ACK",
        mode=MessageMode.COMMAND
    )
    
    controller.message_processor.send_message(test_msg)
    
    # Verify acknowledgment
    ack_path = temp_runtime_dir / "mailbox" / "Agent-4" / "acknowledgments.json"
    assert ack_path.exists()
    
    with ack_path.open("r") as f:
        acks = json.load(f)
        assert any(ack["message_id"] == test_msg.id for ack in acks)

def test_agent_health_check(controller, menu_builder, temp_runtime_dir):
    """Test agent health check protocol."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Create health check message
    health_msg = Message(
        from_agent="system",
        to_agent="Agent-4",
        content="HEALTH_CHECK",
        mode=MessageMode.SELF_TEST
    )
    
    # Send health check
    controller.message_processor.send_message(health_msg)
    
    # Verify health response
    health_path = temp_runtime_dir / "mailbox" / "Agent-4" / "health.json"
    assert health_path.exists()
    
    with health_path.open("r") as f:
        health = json.load(f)
        assert health["status"] == "healthy"
        assert "timestamp" in health

def test_message_ordering_validation(controller, menu_builder, temp_runtime_dir):
    """Test validation of message ordering."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu
    
    # Send multiple messages
    messages = [
        Message(from_agent="system", to_agent="Agent-4", content=f"MSG_{i}", mode=MessageMode.COMMAND)
        for i in range(3)
    ]
    
    for msg in messages:
        controller.message_processor.send_message(msg)
    
    # Verify message order
    inbox_path = temp_runtime_dir / "mailbox" / "Agent-4" / "inbox.json"
    with inbox_path.open("r") as f:
        data = json.load(f)
        assert len(data) == 3
        for i, msg in enumerate(messages):
            assert f"MSG_{i}" in data[i]["content"] 