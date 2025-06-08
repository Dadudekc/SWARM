"""Tests for the cell phone messaging system."""

import pytest
import time
from pathlib import Path
from datetime import datetime
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.enums import MessageMode
from unittest.mock import patch, MagicMock
from dreamos.core.message import Message

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset CellPhone singleton before each test."""
    CellPhone.reset_singleton()
    yield
    # Ensure queue is cleared after each test
    if CellPhone._instance:
        CellPhone._instance.queue.clear_queue()
        CellPhone._instance.shutdown()
    CellPhone.reset_singleton()

@pytest.fixture
def cell_phone():
    """Fixture to provide a CellPhone instance."""
    phone = CellPhone()
    # Clear any existing messages
    phone.queue.clear_queue()
    yield phone
    # Ensure proper cleanup
    phone.queue.clear_queue()
    phone.shutdown()

def test_basic_message_sending(cell_phone):
    """Test basic message sending functionality."""
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    assert success, "Failed to send basic message"
    # Verify queue state
    assert cell_phone.queue.get_queue_size() == 1, "Queue should contain exactly one message"

def test_message_priorities(cell_phone):
    """Test message priority handling."""
    # Test high priority message
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="High priority message",
        mode="PRIORITY",
        priority=5
    )
    assert success, "Failed to send high priority message"
    
    # Test normal priority message
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Normal priority message",
        mode="NORMAL",
        priority=0
    )
    assert success, "Failed to send normal priority message"

def test_message_modes(cell_phone):
    """Test different message modes."""
    modes = ["NORMAL", "PRIORITY", "BULK", "SYSTEM"]
    for mode in modes:
        success = cell_phone.send_message(
            to_agent="Agent-1",
            content=f"Test {mode} message",
            mode=mode,
            priority=0
        )
        assert success, f"Failed to send {mode} message"

def test_rate_limiting(cell_phone):
    """Test message rate limiting."""
    # Send multiple messages quickly
    for i in range(5):
        success = cell_phone.send_message(
            to_agent="Agent-1",
            content=f"Test message {i}",
            mode="NORMAL",
            priority=0
        )
        assert success, f"Failed to send message {i}"

def test_empty_message(cell_phone):
    """Test handling of empty messages."""
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="",
        mode="NORMAL",
        priority=0
    )
    assert not success, "Empty message should be rejected"

def test_invalid_priority(cell_phone):
    """Test handling of invalid priorities."""
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=6  # Invalid priority
    )
    assert not success, "Invalid priority should be rejected"

def test_invalid_message_mode(cell_phone):
    """Test handling of invalid message modes."""
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="INVALID_MODE",
        priority=0
    )
    assert not success, "Invalid message mode should be rejected"

def test_invalid_agent_name(cell_phone):
    """Test handling of invalid agent names."""
    success = cell_phone.send_message(
        to_agent="invalid_agent",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    assert not success, "Invalid agent name should be rejected"

def test_status_tracking(cell_phone):
    """Test message status tracking."""
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    assert success, "Failed to send message"
    
    status = cell_phone.get_message_status("Agent-1")
    assert status is not None
    assert "message_history" in status

def test_concurrent_messages(cell_phone):
    """Test sending messages to multiple agents concurrently."""
    agents = ["Agent-1", "Agent-2", "Agent-3"]
    for agent in agents:
        success = cell_phone.send_message(
            to_agent=agent,
            content=f"Test message for {agent}",
            mode="NORMAL",
            priority=0
        )
        assert success, f"Failed to send message to {agent}"
    # Verify queue state
    assert cell_phone.queue.get_queue_size() == len(agents), f"Queue should contain exactly {len(agents)} messages"

def test_message_history(cell_phone):
    """Test message history tracking."""
    # Clear any existing history
    cell_phone.queue.clear_queue()
    # Send multiple messages
    for i in range(3):
        cell_phone.send_message(
            to_agent="Agent-1",
            content=f"Test message {i}",
            mode="NORMAL",
            priority=0
        )
    
    history = cell_phone.get_message_history("Agent-1")
    assert len(history) == 3, "Message history should contain 3 messages"
    # Verify queue state
    assert cell_phone.queue.get_queue_size() == 3, "Queue should contain exactly 3 messages"

def test_message_validation(cell_phone):
    """Test message validation."""
    # Test valid message
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="Valid message",
        mode="NORMAL",
        priority=0
    )
    assert success, "Valid message should be accepted"
    
    # Test invalid message (empty content)
    success = cell_phone.send_message(
        to_agent="Agent-1",
        content="",
        mode="NORMAL",
        priority=0
    )
    assert not success, "Invalid message should be rejected"

def test_send_message_validation(cell_phone):
    """Test message validation in send_message."""
    # Test invalid agent name
    assert not cell_phone.send_message(
        to_agent="invalid",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    
    # Test invalid priority
    assert not cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=6
    )
    
    # Test invalid mode
    assert not cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="INVALID",
        priority=0
    )
    
    # Test empty message
    assert not cell_phone.send_message(
        to_agent="Agent-1",
        content="",
        mode="NORMAL",
        priority=0
    )

def test_message_queue_operations(cell_phone):
    """Test message queue operations."""
    # Send a message
    cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    
    # Clear messages
    cell_phone.clear_messages("Agent-1")
    
    # Verify queue is empty
    status = cell_phone.get_message_status("Agent-1")
    assert len(status["message_history"]) == 0

def test_shutdown(cell_phone):
    """Test proper shutdown behavior."""
    # Send a test message
    cell_phone.send_message(
        to_agent="Agent-1",
        content="Test message",
        mode="NORMAL",
        priority=0
    )
    # Verify message was queued
    assert cell_phone.queue.get_queue_size() == 1, "Queue should contain one message before shutdown"
    # Shutdown
    cell_phone.shutdown()
    # Verify queue is cleared
    assert cell_phone.queue.get_queue_size() == 0, "Queue should be empty after shutdown"

def test_singleton_behavior():
    """Test singleton behavior of CellPhone."""
    cell_phone1 = CellPhone()
    cell_phone2 = CellPhone()
    
    assert cell_phone1 is cell_phone2
    
    # Test reset
    CellPhone.reset_singleton()
    cell_phone3 = CellPhone()
    assert cell_phone1 is not cell_phone3 
