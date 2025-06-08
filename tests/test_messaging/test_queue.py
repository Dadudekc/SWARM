"""
Tests for PersistentMessageQueue
-------------------------------
Validates queue functionality including:
- Message enqueueing/dequeueing
- Priority ordering
- Persistence
- Error handling
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from dreamos.core.messaging.queue import PersistentMessageQueue
from dreamos.core.messaging.unified_message_system import Message, MessageMode, MessagePriority

@pytest.fixture
async def temp_queue(tmp_path):
    """Create a temporary queue for testing."""
    queue_dir = tmp_path / "queue_store"
    queue = PersistentMessageQueue(queue_dir)
    yield queue
    # Cleanup
    await queue.cleanup()

@pytest.mark.asyncio
async def test_enqueue_and_get(temp_queue):
    """Test basic message enqueueing and retrieval."""
    msg = Message(
        message_id="test-1",
        sender_id="A",
        recipient_id="B",
        content="hello",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await temp_queue.enqueue(msg)
    assert success
    
    messages = await temp_queue.get_messages("B")
    assert len(messages) == 1
    assert messages[0].content == "hello"
    assert messages[0].sender_id == "A"

@pytest.mark.asyncio
async def test_priority_ordering(temp_queue):
    """Test that messages are ordered by priority."""
    high_priority = Message(
        message_id="test-2",
        sender_id="A",
        recipient_id="B",
        content="high",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.HIGH,
        timestamp=datetime.now(),
        metadata={}
    )
    
    low_priority = Message(
        message_id="test-3",
        sender_id="A",
        recipient_id="B",
        content="low",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.LOW,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_queue.enqueue(low_priority)
    await temp_queue.enqueue(high_priority)
    
    messages = await temp_queue.get_messages("B")
    assert len(messages) == 2
    assert messages[0].content == "high"  # High priority first
    assert messages[1].content == "low"

@pytest.mark.asyncio
async def test_acknowledge(temp_queue):
    """Test message acknowledgment."""
    msg = Message(
        message_id="test-4",
        sender_id="A",
        recipient_id="B",
        content="test",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_queue.enqueue(msg)
    success = await temp_queue.acknowledge("test-4")
    assert success
    
    # Message should be marked as processed
    messages = await temp_queue.get_messages("B")
    assert len(messages) == 0

@pytest.mark.asyncio
async def test_persistence(temp_queue):
    """Test that messages persist across queue instances."""
    msg = Message(
        message_id="test-5",
        sender_id="A",
        recipient_id="B",
        content="persist",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_queue.enqueue(msg)
    
    # Create new queue instance
    new_queue = PersistentMessageQueue(temp_queue.queue_dir)
    
    # Message should be loaded from disk
    messages = await new_queue.get_messages("B")
    assert len(messages) == 1
    assert messages[0].content == "persist"

@pytest.mark.asyncio
async def test_empty_queue(temp_queue):
    """Test behavior with empty queue."""
    messages = await temp_queue.get_messages("nonexistent")
    assert len(messages) == 0

@pytest.mark.asyncio
async def test_multiple_recipients(temp_queue):
    """Test handling messages for multiple recipients."""
    msg1 = Message(
        message_id="test-6",
        sender_id="A",
        recipient_id="B",
        content="to B",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    msg2 = Message(
        message_id="test-7",
        sender_id="A",
        recipient_id="C",
        content="to C",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_queue.enqueue(msg1)
    await temp_queue.enqueue(msg2)
    
    messages_b = await temp_queue.get_messages("B")
    messages_c = await temp_queue.get_messages("C")
    
    assert len(messages_b) == 1
    assert len(messages_c) == 1
    assert messages_b[0].content == "to B"
    assert messages_c[0].content == "to C" 
