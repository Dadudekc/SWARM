import pytest
import asyncio
from datetime import datetime
from dreamos.core.messaging.unified_message_system import MessageSystem
from dreamos.core.messaging.common import Message
from dreamos.core.messaging.enums import MessageMode, MessagePriority, MessageType

@pytest.fixture
def message_system():
    """Create a test message system instance."""
    return MessageSystem()

@pytest.mark.asyncio
async def test_io_message_handling(message_system):
    """Test basic IO message handling."""
    # Send an IO message
    success = await message_system.send(
        to_agent="io_agent",
        content="Test IO message",
        mode=MessageMode.DIRECT,
        priority=MessagePriority.NORMAL,
        from_agent="test_sender",
        metadata={"io_type": "test"}
    )
    assert success

    # Verify message was received
    messages = await message_system.receive("io_agent")
    assert len(messages) == 1
    message = messages[0]
    assert message.content == "Test IO message"
    assert message.metadata.get("io_type") == "test"

@pytest.mark.asyncio
async def test_io_message_processing(message_system):
    """Test IO message processing with handlers."""
    processed_messages = []
    
    async def io_handler(message: Message):
        processed_messages.append(message)
        # Simulate IO processing
        await asyncio.sleep(0.1)
    
    # Subscribe to IO messages
    await message_system.subscribe("io_agent", io_handler)
    
    # Send multiple IO messages
    for i in range(3):
        await message_system.send(
            to_agent="io_agent",
            content=f"IO message {i}",
            mode=MessageMode.DIRECT,
            priority=MessagePriority.NORMAL,
            metadata={"io_type": "test"}
        )
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Verify all messages were processed
    assert len(processed_messages) == 3
    for i, message in enumerate(processed_messages):
        assert message.content == f"IO message {i}"

@pytest.mark.asyncio
async def test_io_message_priority(message_system):
    """Test IO message priority handling."""
    # Send messages with different priorities
    await message_system.send(
        to_agent="io_agent",
        content="Low priority",
        mode=MessageMode.DIRECT,
        priority=MessagePriority.LOW
    )
    
    await message_system.send(
        to_agent="io_agent",
        content="High priority",
        mode=MessageMode.DIRECT,
        priority=MessagePriority.HIGH
    )
    
    # Get messages
    messages = await message_system.receive("io_agent")
    assert len(messages) == 2
    
    # Verify high priority message is first
    assert messages[0].content == "High priority"
    assert messages[0].priority == MessagePriority.HIGH
    assert messages[1].content == "Low priority"
    assert messages[1].priority == MessagePriority.LOW

@pytest.mark.asyncio
async def test_io_message_error_handling(message_system):
    """Test IO message error handling."""
    # Send an invalid message
    success = await message_system.send(
        to_agent="io_agent",
        content="",  # Empty content should be invalid
        mode=MessageMode.DIRECT,
        priority=MessagePriority.NORMAL
    )
    
    # Message should still be sent but marked as invalid
    messages = await message_system.receive("io_agent")
    assert len(messages) == 1
    assert not messages[0].validate()  # Should fail validation 