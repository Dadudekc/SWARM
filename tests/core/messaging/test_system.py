"""
Tests for the unified message system.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from dreamos.core.messaging.base import Message, MessageType, MessagePriority
from dreamos.core.messaging.system import MessageSystem

@pytest.fixture
async def message_system():
    """Create a message system for testing."""
    system = MessageSystem()
    await system.start()
    yield system
    await system.stop()

@pytest.fixture
def test_message():
    """Create a test message."""
    return Message(
        id="test-1",
        type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        sender="test-sender",
        recipient="test-recipient",
        content="test content",
        metadata={"test": "data"}
    )

@pytest.mark.asyncio
async def test_send_message(message_system, test_message):
    """Test sending a message."""
    # Add route
    message_system.add_route("test-sender", {"test-recipient"})
    
    # Add handler
    received = []
    async def handler(message):
        received.append(message)
        return True
    message_system.add_handler(MessageType.COMMAND, handler)
    
    # Send message
    success = await message_system.send(test_message)
    assert success
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 1
    assert received[0].id == test_message.id

@pytest.mark.asyncio
async def test_broadcast_message(message_system, test_message):
    """Test broadcasting a message."""
    # Add routes
    message_system.add_route("test-sender", {"recipient-1", "recipient-2"})
    
    # Add handlers
    received = []
    async def handler(message):
        received.append(message)
        return True
    message_system.add_handler(MessageType.COMMAND, handler)
    
    # Broadcast message
    count = await message_system.broadcast(test_message)
    assert count == 2
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 2

@pytest.mark.asyncio
async def test_rate_limiting(message_system, test_message):
    """Test message rate limiting."""
    # Set rate limit
    message_system.set_rate_limit("test-sender", 2, timedelta(seconds=1))
    
    # Add route and handler
    message_system.add_route("test-sender", {"test-recipient"})
    received = []
    async def handler(message):
        received.append(message)
        return True
    message_system.add_handler(MessageType.COMMAND, handler)
    
    # Send messages
    for _ in range(3):
        await message_system.send(test_message)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 2  # Only 2 messages should get through

@pytest.mark.asyncio
async def test_content_validation(message_system):
    """Test message content validation."""
    # Set content pattern
    message_system.set_content_pattern(MessageType.COMMAND, r"^valid.*$")
    
    # Add route and handler
    message_system.add_route("test-sender", {"test-recipient"})
    received = []
    async def handler(message):
        received.append(message)
        return True
    message_system.add_handler(MessageType.COMMAND, handler)
    
    # Send valid message
    valid_message = Message(
        id="test-1",
        type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        sender="test-sender",
        recipient="test-recipient",
        content="valid content",
        metadata={}
    )
    success = await message_system.send(valid_message)
    assert success
    
    # Send invalid message
    invalid_message = Message(
        id="test-2",
        type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        sender="test-sender",
        recipient="test-recipient",
        content="invalid content",
        metadata={}
    )
    success = await message_system.send(invalid_message)
    assert not success
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 1
    assert received[0].id == valid_message.id

@pytest.mark.asyncio
async def test_required_fields(message_system, test_message):
    """Test required fields validation."""
    # Set required fields
    message_system.set_required_fields(MessageType.COMMAND, {"required_field"})
    
    # Add route and handler
    message_system.add_route("test-sender", {"test-recipient"})
    received = []
    async def handler(message):
        received.append(message)
        return True
    message_system.add_handler(MessageType.COMMAND, handler)
    
    # Send message without required field
    success = await message_system.send(test_message)
    assert not success
    
    # Send message with required field
    test_message.metadata["required_field"] = "value"
    success = await message_system.send(test_message)
    assert success
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 1

@pytest.mark.asyncio
async def test_error_handling(message_system, test_message):
    """Test error handling."""
    # Add route and handler that raises an error
    message_system.add_route("test-sender", {"test-recipient"})
    error_received = []
    async def error_handler(message):
        error_received.append(message)
        return True
    message_system.add_handler(MessageType.ERROR, error_handler)
    
    async def failing_handler(message):
        raise ValueError("Test error")
    message_system.add_handler(MessageType.COMMAND, failing_handler)
    
    # Send message
    success = await message_system.send(test_message)
    assert success
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(error_received) == 1
    assert error_received[0].type == MessageType.ERROR
    assert "Test error" in error_received[0].content
    assert error_received[0].metadata["original_message_id"] == test_message.id

@pytest.mark.asyncio
async def test_default_handler(message_system, test_message):
    """Test default message handler."""
    # Add route
    message_system.add_route("test-sender", {"test-recipient"})
    
    # Add default handler
    received = []
    async def default_handler(message):
        received.append(message)
        return True
    message_system.set_default_handler(default_handler)
    
    # Send message with unknown type
    test_message.type = MessageType.UNKNOWN
    success = await message_system.send(test_message)
    assert success
    
    # Wait for processing
    await asyncio.sleep(0.1)
    assert len(received) == 1
    assert received[0].id == test_message.id 