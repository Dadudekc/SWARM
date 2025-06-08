"""
Tests for PersistentMessageHistory
--------------------------------
Validates history functionality including:
- Message recording
- History retrieval
- Filtering
- Persistence
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dreamos.core.messaging.history import PersistentMessageHistory
from dreamos.core.messaging.unified_message_system import Message, MessageMode, MessagePriority

@pytest.fixture
async def temp_history(tmp_path):
    """Create a temporary history store for testing."""
    history_dir = tmp_path / "history_store"
    history = PersistentMessageHistory(history_dir)
    yield history
    # Cleanup
    await history.cleanup()

@pytest.mark.asyncio
async def test_record_and_retrieve(temp_history):
    """Test basic message recording and retrieval."""
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
    
    success = await temp_history.record(msg)
    assert success
    
    history = await temp_history.get_history()
    assert len(history) == 1
    assert history[0].content == "hello"
    assert history[0].sender_id == "A"

@pytest.mark.asyncio
async def test_filter_by_agent(temp_history):
    """Test filtering history by agent."""
    msg1 = Message(
        message_id="test-2",
        sender_id="A",
        recipient_id="B",
        content="A to B",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    msg2 = Message(
        message_id="test-3",
        sender_id="B",
        recipient_id="C",
        content="B to C",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_history.record(msg1)
    await temp_history.record(msg2)
    
    # Filter by sender
    sender_history = await temp_history.get_history(agent_id="A")
    assert len(sender_history) == 1
    assert sender_history[0].content == "A to B"
    
    # Filter by recipient
    recipient_history = await temp_history.get_history(agent_id="C")
    assert len(recipient_history) == 1
    assert recipient_history[0].content == "B to C"

@pytest.mark.asyncio
async def test_filter_by_time(temp_history):
    """Test filtering history by time range."""
    now = datetime.now()
    past = now - timedelta(hours=1)
    future = now + timedelta(hours=1)
    
    msg1 = Message(
        message_id="test-4",
        sender_id="A",
        recipient_id="B",
        content="past",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=past,
        metadata={}
    )
    
    msg2 = Message(
        message_id="test-5",
        sender_id="A",
        recipient_id="B",
        content="now",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=now,
        metadata={}
    )
    
    msg3 = Message(
        message_id="test-6",
        sender_id="A",
        recipient_id="B",
        content="future",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=future,
        metadata={}
    )
    
    await temp_history.record(msg1)
    await temp_history.record(msg2)
    await temp_history.record(msg3)
    
    # Filter by time range
    recent = await temp_history.get_history(
        start_time=past,
        end_time=now
    )
    assert len(recent) == 2
    assert recent[0].content == "past"
    assert recent[1].content == "now"

@pytest.mark.asyncio
async def test_limit_results(temp_history):
    """Test limiting number of results."""
    for i in range(5):
        msg = Message(
            message_id=f"test-{i}",
            sender_id="A",
            recipient_id="B",
            content=f"msg {i}",
            mode=MessageMode.NORMAL,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            metadata={}
        )
        await temp_history.record(msg)
    
    limited = await temp_history.get_history(limit=3)
    assert len(limited) == 3
    assert limited[0].content == "msg 2"  # Most recent first
    assert limited[1].content == "msg 3"
    assert limited[2].content == "msg 4"

@pytest.mark.asyncio
async def test_persistence(temp_history):
    """Test that history persists across instances."""
    msg = Message(
        message_id="test-7",
        sender_id="A",
        recipient_id="B",
        content="persist",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    await temp_history.record(msg)
    
    # Create new history instance
    new_history = PersistentMessageHistory(temp_history.history_dir)
    
    # Message should be loaded from disk
    history = await new_history.get_history()
    assert len(history) == 1
    assert history[0].content == "persist"

@pytest.mark.asyncio
async def test_max_history(temp_history):
    """Test that history respects maximum size limit."""
    # Set small max history for testing
    temp_history.max_history = 3
    
    for i in range(5):
        msg = Message(
            message_id=f"test-{i}",
            sender_id="A",
            recipient_id="B",
            content=f"msg {i}",
            mode=MessageMode.NORMAL,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            metadata={}
        )
        await temp_history.record(msg)
    
    history = await temp_history.get_history()
    assert len(history) == 3
    assert history[0].content == "msg 2"  # Most recent messages kept
    assert history[1].content == "msg 3"
    assert history[2].content == "msg 4" 
