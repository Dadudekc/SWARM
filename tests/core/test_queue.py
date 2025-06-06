import pytest
from dreamos.core.persistent_queue import PersistentQueue
from dreamos.core.messaging.message import Message
from dreamos.core.messaging.enums import MessageMode
import os
import json
from datetime import datetime

@pytest.fixture
def queue(tmp_path):
    """Create a test queue instance."""
    queue_path = tmp_path / "test_queue.json"
    return PersistentQueue(str(queue_path))

def test_queue_initialization(queue):
    """Test queue initialization."""
    assert queue is not None
    assert queue.get_queue_size() == 0

def test_add_message(queue):
    """Test adding a message to the queue."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    assert queue.get_queue_size() == 1

def test_get_message(tmp_path):
    """Test getting a message from the queue."""
    queue_path = tmp_path / "test_queue_get.json"
    queue = PersistentQueue(str(queue_path))
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.put(message)
    retrieved = queue.get()
    assert retrieved.content == message.content
    assert retrieved.from_agent == message.from_agent
    assert retrieved.to_agent == message.to_agent
    assert retrieved.mode == message.mode

def test_clear_queue(queue):
    """Test clearing the queue."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    queue.clear_queue()
    assert queue.get_queue_size() == 0

def test_persistent_storage(queue):
    """Test that messages persist between queue instances."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    
    # Create new queue instance with same path
    new_queue = PersistentQueue(queue.queue_path)
    assert new_queue.get_queue_size() == 1
    retrieved = new_queue.get_message()
    assert retrieved.content == message.content
    assert retrieved.from_agent == message.from_agent
    assert retrieved.to_agent == message.to_agent
    assert retrieved.mode == message.mode

def test_message_priority(queue):
    """Test message priority handling."""
    high_priority = Message(
        content="High priority",
        mode=MessageMode.PRIORITY,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now(),
        priority=1
    )
    normal_priority = Message(
        content="Normal priority",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now(),
        priority=5
    )
    
    queue.put(normal_priority)
    queue.put(high_priority)
    
    # High priority message should be retrieved first
    first = queue.get()
    assert first.content == high_priority.content
    assert first.mode == high_priority.mode
    second = queue.get()
    assert second.content == normal_priority.content
    assert second.mode == normal_priority.mode

def test_queue_size_limit(queue):
    """Test queue size limit handling."""
    # Enable test mode to disable rate limiting
    queue.set_test_mode(True)
    
    # Add messages until queue is full
    for i in range(queue.max_size + 1):
        message = Message(
            content=f"Message {i}",
            mode=MessageMode.NORMAL,
            from_agent="test_sender",
            to_agent="test_recipient",
            timestamp=datetime.now()
        )
        queue.add_message(message)
    
    assert queue.get_queue_size() == queue.max_size

def test_invalid_message(queue):
    """Test handling of invalid messages."""
    with pytest.raises(ValueError):
        queue.add_message(None)
    
    with pytest.raises(ValueError):
        queue.add_message("not a message")

def test_empty_queue(queue):
    """Test behavior when queue is empty."""
    assert queue.get_message() is None
    assert queue.get_queue_size() == 0

def test_message_history(queue):
    """Test message history tracking."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    queue.get_message()  # Process the message
    
    history = queue.get_message_history()
    assert len(history) == 1
    assert history[0].content == message.content
    assert history[0].from_agent == message.from_agent
    assert history[0].to_agent == message.to_agent
    assert history[0].mode == message.mode

def test_clear_history(queue):
    """Test clearing message history."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    queue.get_message()  # Process the message
    
    queue.clear_history()
    assert len(queue.get_message_history()) == 0

def test_queue_status(queue):
    """Test queue status reporting."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.put(message)
    
    status = queue.get_status()
    assert status["queue_size"] == 1
    assert status["history_size"] == 1
    assert len(status["messages"]) == 1

def test_queue_shutdown(queue):
    """Test proper queue shutdown."""
    message = Message(
        content="Test message",
        mode=MessageMode.NORMAL,
        from_agent="test_sender",
        to_agent="test_recipient",
        timestamp=datetime.now()
    )
    queue.add_message(message)
    
    queue.shutdown()
    assert queue.get_queue_size() == 0
    assert len(queue.get_message_history()) == 0 