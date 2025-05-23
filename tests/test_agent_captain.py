import pytest
from unittest.mock import MagicMock, patch
from dreamos.core.agent_captain import AgentCaptain
from agent_tools.agent_cellphone import MessageMode

@pytest.fixture
def agent_captain():
    return AgentCaptain()

def test_send_message(agent_captain):
    # Mock the cursor controller
    agent_captain.cursor = MagicMock()
    agent_captain.coords = {
        "Agent-1": {
            "input_box": (100, 100),
            "initial_spot": (200, 200),
            "copy_button": (300, 300)
        }
    }
    
    # Test sending a message
    result = agent_captain.send_message("Agent-1", "Hello", MessageMode.NORMAL)
    assert result is True
    
    # Verify cursor interactions
    assert agent_captain.cursor.move_to.call_count >= 4  # At least 3 moves for focus + 1 for final click
    assert agent_captain.cursor.click.call_count >= 4
    assert agent_captain.cursor.type_text.call_count == 1
    assert agent_captain.cursor.press_enter.call_count == 1

def test_get_agent_status(agent_captain):
    # Mock the cell phone
    agent_captain.cell_phone = MagicMock()
    agent_captain.cell_phone.get_queue_status.return_value = {
        "Agent-1": {
            "agent_id": "Agent-1",
            "coordinates_available": True,
            "last_message_sent": True,
            "timestamp": "2025-05-23 03:52:11"
        }
    }
    
    # Test getting agent status
    status = agent_captain.get_agent_status("Agent-1")
    assert isinstance(status, dict)
    assert status["agent_id"] == "Agent-1"
    assert status["coordinates_available"] is True
    assert status["last_message_sent"] is True
    assert "timestamp" in status

def test_clear_agent_messages(agent_captain):
    # Mock the cell phone
    agent_captain.cell_phone = MagicMock()
    agent_captain.clear_agent_messages("Agent-1")
    agent_captain.cell_phone.clear_messages.assert_called_once_with("Agent-1") 