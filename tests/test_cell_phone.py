"""
Pytest test suite for cell phone functionality.
Tests message sending, modes, priorities, and rate limiting.
"""

import pytest
import time
from datetime import datetime
from dreamos.core import CellPhone, MessageMode

@pytest.fixture
def cell_phone():
    """Fixture to provide a CellPhone instance."""
    phone = CellPhone()
    yield phone
    phone.shutdown()

def test_basic_message_sending(cell_phone):
    """Test basic message sending functionality."""
    success = cell_phone.send_message(
        from_agent="test",
        to_agent="Agent-1",
        message="Hello from test script!",
        priority=0
    )
    assert success, "Basic message should send successfully"
    
    status = cell_phone.get_status()
    assert status["queue_size"] >= 0, "Queue size should be non-negative"

def test_message_priorities(cell_phone):
    """Test message priority handling."""
    # Test each priority level
    for priority in range(6):  # 0-5
        success = cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-2",
            message=f"Priority {priority} test message",
            priority=priority
        )
        assert success, f"Message with priority {priority} should send successfully"

def test_message_modes(cell_phone):
    """Test different message modes."""
    modes = [
        (MessageMode.RESUME, "Initiating autonomous protocol"),
        (MessageMode.SYNC, "Requesting status update"),
        (MessageMode.VERIFY, "Please verify current state"),
        (MessageMode.TASK, "New task assignment"),
        (MessageMode.INTEGRATE, "Begin system integration"),
        (MessageMode.CLEANUP, "Initiating system cleanup"),
        (MessageMode.BACKUP, "Please backup current state"),
        (MessageMode.RESTORE, "Restore from backup"),
        (MessageMode.CAPTAIN, "Captain mode activated"),
        (MessageMode.NORMAL, "Normal message")
    ]
    
    for mode, message in modes:
        success = cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-3",
            message=f"{mode.value} {message}",
            priority=2
        )
        assert success, f"Message with mode {mode.name} should send successfully"

def test_rate_limiting(cell_phone):
    """Test rate limiting functionality."""
    # Send multiple messages quickly
    successes = []
    for i in range(5):
        success = cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-4",
            message=f"Rate limit test message {i+1}",
            priority=1
        )
        successes.append(success)
        time.sleep(0.1)  # Small delay between messages
    
    # At least some messages should succeed
    assert any(successes), "Some messages should succeed despite rate limiting"

def test_invalid_priority(cell_phone):
    """Test handling of invalid priority values."""
    with pytest.raises(ValueError):
        cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-5",
            message="Invalid priority test",
            priority=6  # Invalid priority
        )

def test_empty_message(cell_phone):
    """Test handling of empty messages."""
    with pytest.raises(ValueError):
        cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-6",
            message="",  # Empty message
            priority=0
        )

def test_status_tracking(cell_phone):
    """Test message status tracking."""
    # Send a message
    cell_phone.send_message(
        from_agent="test",
        to_agent="Agent-7",
        message="Status tracking test",
        priority=2
    )
    
    # Get status
    status = cell_phone.get_status()
    assert isinstance(status, dict), "Status should be a dictionary"
    assert "queue_size" in status, "Status should include queue size"
    assert "last_message" in status, "Status should include last message info"

def test_concurrent_messages(cell_phone):
    """Test sending messages to multiple agents concurrently."""
    agents = [f"Agent-{i}" for i in range(1, 4)]
    successes = []
    
    for agent in agents:
        success = cell_phone.send_message(
            from_agent="test",
            to_agent=agent,
            message=f"Concurrent test message to {agent}",
            priority=1
        )
        successes.append(success)
    
    assert all(successes), "All concurrent messages should send successfully"

def test_message_history(cell_phone):
    """Test message history tracking."""
    # Send multiple messages
    for i in range(3):
        cell_phone.send_message(
            from_agent="test",
            to_agent="Agent-8",
            message=f"History test message {i+1}",
            priority=1
        )
    
    # Get status and check history
    status = cell_phone.get_status()
    assert "message_history" in status, "Status should include message history"
    assert len(status["message_history"]) >= 3, "History should track sent messages" 