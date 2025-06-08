"""
Tests for UnifiedMessageSystem
----------------------------
Validates the unified message system including:
- Message sending/receiving
- Subscriptions
- History integration
- Queue integration
- Router integration
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from dreamos.core.messaging.unified_message_system import (
    UnifiedMessageSystem,
    Message,
    MessageMode,
    MessagePriority
)
from dreamos.core.messaging.queue import PersistentMessageQueue
from dreamos.core.messaging.history import PersistentMessageHistory
from dreamos.core.messaging.router import MessageRouter

@pytest.fixture
async def temp_system(tmp_path):
    """Create a temporary message system for testing."""
    runtime_dir = tmp_path / "runtime"
    queue_dir = runtime_dir / "queues"
    history_dir = runtime_dir / "history"
    
    queue = PersistentMessageQueue(queue_dir)
    history = PersistentMessageHistory(history_dir)
    router = MessageRouter()
    
    system = UnifiedMessageSystem(
        runtime_dir=runtime_dir,
        queue=queue,
        history=history,
        router=router
    )
    
    yield system
    
    # Cleanup
    await system.cleanup()

@pytest.mark.asyncio
async def test_send_and_receive(temp_system):
    """Test basic message sending and receiving."""
    success = await temp_system.send(
        to_agent="B",
        content="hello",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        from_agent="A"
    )
    assert success
    
    messages = await temp_system.receive("B")
    assert len(messages) == 1
    assert messages[0].content == "hello"
    assert messages[0].sender_id == "A"

@pytest.mark.asyncio
async def test_subscription(temp_system):
    """Test message subscriptions."""
    received = False
    
    async def handle_message(message: Message):
        nonlocal received
        received = True
        assert message.content == "subscribed"
    
    await temp_system.subscribe("B", handle_message)
    
    await temp_system.send(
        to_agent="B",
        content="subscribed",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    
    # Give time for subscription to process
    await asyncio.sleep(0.1)
    assert received

@pytest.mark.asyncio
async def test_pattern_subscription(temp_system):
    """Test pattern-based subscriptions."""
    received = False
    
    async def handle_message(message: Message):
        nonlocal received
        received = True
        assert message.content == "pattern"
    
    await temp_system.subscribe_pattern("agent-.*", handle_message)
    
    await temp_system.send(
        to_agent="agent-1",
        content="pattern",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    
    # Give time for subscription to process
    await asyncio.sleep(0.1)
    assert received

@pytest.mark.asyncio
async def test_history_integration(temp_system):
    """Test history recording and retrieval."""
    await temp_system.send(
        to_agent="B",
        content="history",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        from_agent="A"
    )
    
    history = await temp_system.get_history(agent_id="B")
    assert len(history) == 1
    assert history[0].content == "history"
    assert history[0].sender_id == "A"

@pytest.mark.asyncio
async def test_priority_handling(temp_system):
    """Test message priority handling."""
    await temp_system.send(
        to_agent="B",
        content="low",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.LOW,
        from_agent="A"
    )
    
    await temp_system.send(
        to_agent="B",
        content="high",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.HIGH,
        from_agent="A"
    )
    
    messages = await temp_system.receive("B")
    assert len(messages) == 2
    assert messages[0].content == "high"  # High priority first
    assert messages[1].content == "low"

@pytest.mark.asyncio
async def test_mode_handling(temp_system):
    """Test different message modes."""
    handled = False
    
    async def handle_command(message: Message, target: str) -> bool:
        nonlocal handled
        handled = True
        return True
    
    temp_system.router.add_mode_handler(MessageMode.COMMAND, handle_command)
    
    await temp_system.send(
        to_agent="B",
        content="command",
        mode=MessageMode.COMMAND,
        priority=MessagePriority.NORMAL
    )
    
    assert handled

@pytest.mark.asyncio
async def test_persistence(temp_system):
    """Test system persistence across restarts."""
    await temp_system.send(
        to_agent="B",
        content="persist",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    
    # Create new system instance
    new_system = UnifiedMessageSystem(
        runtime_dir=temp_system.runtime_dir,
        queue=PersistentMessageQueue(temp_system.queue.queue_dir),
        history=PersistentMessageHistory(temp_system.history.history_dir),
        router=MessageRouter()
    )
    
    # Message should be in queue
    messages = await new_system.receive("B")
    assert len(messages) == 1
    assert messages[0].content == "persist"
    
    # Message should be in history
    history = await new_system.get_history(agent_id="B")
    assert len(history) == 1
    assert history[0].content == "persist"

@pytest.mark.asyncio
async def test_error_handling(temp_system):
    """Test error handling in message processing."""
    # Test with invalid message
    success = await temp_system.send(
        to_agent="",  # Invalid recipient
        content="error",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    assert not success
    
    # Test with failing handler
    async def failing_handler(message: Message, target: str) -> bool:
        return False
    
    temp_system.router.add_mode_handler(MessageMode.SYSTEM, failing_handler)
    
    success = await temp_system.send(
        to_agent="B",
        content="fail",
        mode=MessageMode.SYSTEM,
        priority=MessagePriority.NORMAL
    )
    assert not success 
