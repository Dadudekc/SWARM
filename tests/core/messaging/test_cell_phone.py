"""Tests for cell_phone module."""

import pytest
import os
import json
import tempfile
from pathlib import Path
from dreamos.core.messaging.cell_phone import (
    validate_phone_number,
    format_phone_number,
    send_message,
    CellPhone,
    CaptainPhone,
    MessageMode,
    MessageQueue
)
from unittest.mock import patch

# Mock coordinate data
MOCK_COORDS = {
    "test_agent": {
        "x": 123,
        "y": 456
    },
    "agent-1": {
        "x": 100,
        "y": 200
    }
}

@pytest.fixture
def temp_coord_file():
    """Create a temporary coordinate file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        json.dump(MOCK_COORDS, f)
        f.flush()  # Ensure data is written
        yield f.name
        # Cleanup after test
        try:
            os.remove(f.name)
        except OSError:
            pass  # Ignore cleanup errors

@pytest.fixture
def cell_phone(temp_coord_file):
    """Create a CellPhone instance with a temporary coordinate file."""
    return CellPhone({"coordinate_file": temp_coord_file})

@pytest.fixture
def captain_phone(temp_coord_file):
    """Create a CaptainPhone instance with a temporary coordinate file."""
    return CaptainPhone({"coordinate_file": temp_coord_file})

@pytest.fixture
def temp_queue_file():
    """Create a temporary queue file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        json.dump([], f)  # Initialize with empty list
        f.flush()
        yield f.name
        try:
            os.remove(f.name)
        except OSError:
            pass

@pytest.fixture
def message_queue(temp_queue_file):
    """Create a MessageQueue instance with a temporary file."""
    return MessageQueue(temp_queue_file)

def test_validate_phone_number():
    """Test phone number validation."""
    assert validate_phone_number("1234567890") is True
    assert validate_phone_number("+1-234-567-8901") is True
    assert validate_phone_number("(123) 456-7890") is True
    assert validate_phone_number("invalid") is False
    assert validate_phone_number("") is False

def test_format_phone_number():
    """Test phone number formatting."""
    assert format_phone_number("1234567890") == "(123) 456-7890"
    assert format_phone_number("+1-234-567-8901") == "(234) 567-8901"
    assert format_phone_number("(123) 456-7890") == "(123) 456-7890"
    assert format_phone_number("invalid") == "invalid"

def ensure_test_inbox(agent_id="test_agent"):
    """Ensure test agent inbox exists."""
    inbox_path = Path(f"agent_tools/mailbox/{agent_id}/inbox.json")
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    if not inbox_path.exists():
        with inbox_path.open("w", encoding="utf-8") as f:
            json.dump({"messages": []}, f)

def test_message_queue_operations(message_queue, temp_queue_file):
    """Test MessageQueue operations."""
    # Test initial state
    assert message_queue.get_messages() == []
    
    # Test adding messages
    message1 = {"content": "test1", "timestamp": "2024-01-01T00:00:00Z"}
    message2 = {"content": "test2", "timestamp": "2024-01-01T00:00:01Z"}
    
    message_queue.add_message(message1)
    assert len(message_queue.get_messages()) == 1
    assert message_queue.get_messages()[0] == message1
    
    message_queue.add_message(message2)
    assert len(message_queue.get_messages()) == 2
    assert message_queue.get_messages()[1] == message2
    
    # Test clearing queue
    message_queue.clear_queue()
    assert message_queue.get_messages() == []
    
    # Test persistence
    new_queue = MessageQueue(temp_queue_file)
    assert new_queue.get_messages() == []

@pytest.mark.asyncio
async def test_send_message():
    """Test sending a message."""
    ensure_test_inbox()
    result = await send_message("test_agent", "Test message", "NORMAL", "test_sender")
    assert result is True

def test_cell_phone_initialization(temp_coord_file):
    """Test CellPhone initialization."""
    # Test default initialization
    phone = CellPhone()
    assert phone.config == {}
    assert phone.coordinates == {}
    
    # Test with mock coordinates
    phone = CellPhone({"coordinate_file": temp_coord_file})
    assert phone.config == {"coordinate_file": temp_coord_file}
    assert "test_agent" in phone.coordinates
    assert phone.coordinates["test_agent"]["x"] == 123
    assert phone.coordinates["test_agent"]["y"] == 456

@pytest.mark.asyncio
async def test_cell_phone_inject_prompt(cell_phone):
    """Test injecting prompts."""
    result = await cell_phone.inject_prompt("test_agent", "test prompt")
    assert result is True

@pytest.mark.asyncio
async def test_send_message_to_missing_agent():
    """Test sending message to non-existent agent."""
    result = await send_message("non_existent_agent", "Test message", "NORMAL", "test_sender")
    assert result is False

@pytest.mark.asyncio
async def test_inject_prompt_fallback_behavior(cell_phone):
    """Test fallback behavior when coordinates are missing."""
    result = await cell_phone.inject_prompt("non_existent_agent", "test prompt")
    assert result is False

def test_recover_from_corrupt_coord_file():
    """Test recovery from corrupt coordinate file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        f.write("invalid json content")
        f.flush()
        corrupt_file = f.name
    
    try:
        phone = CellPhone({"coordinate_file": corrupt_file})
        assert phone.coordinates == {}  # Should recover gracefully with empty coordinates
    finally:
        try:
            os.remove(corrupt_file)
        except OSError:
            pass

def test_captain_phone_singleton():
    """Test CaptainPhone singleton pattern."""
    phone1 = CaptainPhone()
    phone2 = CaptainPhone()
    assert phone1 is phone2
    
    # Test reset
    CaptainPhone.reset_singleton()
    phone3 = CaptainPhone()
    assert phone3 is not phone1

@pytest.mark.asyncio
async def test_captain_phone_broadcast():
    """Test broadcasting messages."""
    phone = CaptainPhone()
    result = await phone.broadcast_message("Test broadcast")
    assert result is True

def test_queue_load_malformed_file():
    """Test queue recovery from malformed file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        f.write("{ this is not json }")
        f.flush()
        path = f.name
    
    try:
        with pytest.raises(json.JSONDecodeError):
            queue = MessageQueue(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_cell_phone_missing_coordinate_keys():
    """Test handling of coordinate file with missing keys."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        json.dump({
            "test_agent": {
                "x": 123  # Missing 'y' coordinate
            }
        }, f)
        f.flush()
        path = f.name
    
    try:
        phone = CellPhone({"coordinate_file": path})
        # Should fail gracefully when trying to use incomplete coordinates
        result = await phone.inject_prompt("test_agent", "test prompt")
        assert result is False
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_cell_phone_invalid_coordinate_values():
    """Test handling of invalid coordinate values."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
        json.dump({
            "test_agent": {
                "x": "not_a_number",  # Invalid type
                "y": 456
            }
        }, f)
        f.flush()
        path = f.name
    
    try:
        phone = CellPhone({"coordinate_file": path})
        # Should fail gracefully when trying to use invalid coordinates
        result = await phone.inject_prompt("test_agent", "test prompt")
        assert result is False
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

@pytest.mark.asyncio
async def test_inject_prompt_missing_coordinates():
    """Test that inject_prompt fails gracefully when coordinates are missing."""
    phone = CellPhone()
    phone.coordinates = {}
    result = await phone.inject_prompt("test_agent", "hello")
    assert result is False

@pytest.mark.asyncio
@pytest.mark.parametrize("x, y, expected", [
    (-1, 200, True),        # Negative x is valid (left of screen)
    (200, -1, True),        # Negative y is valid (above screen)
    (float("inf"), 100, False),  # Infinity is invalid
    ("", 100, False),       # Empty string is invalid
    (1e9, 100, True),       # Large but valid number
    (None, 100, False),     # None is invalid
    (100, None, False),     # None is invalid
    (0, 0, True),          # Origin is valid
])
async def test_coordinate_edge_cases(x, y, expected):
    """Test various edge cases for coordinate values."""
    phone = CellPhone()
    phone.coordinates = {"test_agent": {"x": x, "y": y}}
    
    # Mock pyautogui to avoid actual mouse movement
    with patch("pyautogui.click") as mock_click:
        result = await phone.inject_prompt("test_agent", "test")
        assert result is expected
        
        if expected:
            mock_click.assert_called_once_with(x, y)
        else:
            mock_click.assert_not_called()
