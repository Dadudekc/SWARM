"""
Verification test for Agent-3's message handling with self-test protocol.
"""

import pytest
from unittest.mock import Mock, patch
from dreamos.core.messaging.message import Message, MessageMode
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.agent_control.menu_builder import MenuBuilder

@pytest.fixture
def temp_runtime_dir(tmp_path):
    return tmp_path / "runtime"

@pytest.fixture
def message_processor(temp_runtime_dir):
    from dreamos.core.messaging.message_processor import MessageProcessor
    return MessageProcessor(temp_runtime_dir)

@pytest.fixture
def agent_operations(message_processor):
    from dreamos.core.agent_control.agent_operations import AgentOperations
    return AgentOperations(message_processor)

@pytest.fixture
def controller(agent_operations):
    return AgentController(agent_operations)

@pytest.fixture
def menu_builder(controller):
    return MenuBuilder(controller)

def test_agent3_verification(controller, menu_builder, temp_runtime_dir):
    """Test Agent-3's message handling with self-test protocol."""
    # Setup menu with status panel
    mock_menu = Mock()
    mock_menu._status_panel = Mock()
    mock_menu._status_panel.update_status = Mock()
    menu_builder.menu = mock_menu

    # Create verification message
    verify_msg = Message(
        from_agent="system",
        to_agent="Agent-3",
        content="SUCCESS - Self-test protocol verification complete",
        mode=MessageMode.SELF_TEST
    )

    # Mock pyguiauto interactions
    with patch('pyguiauto.click') as mock_click, patch('pyguiauto.write') as mock_write:
        # Send verification message
        controller.message_processor.send_message(verify_msg)

        # Verify pyguiauto interactions
        mock_click.assert_called_once()
        mock_write.assert_called_once_with(verify_msg.format_content())

    # Verify status panel update
    mock_menu._status_panel.update_status.assert_called_once_with("Message sent to Agent-3") 