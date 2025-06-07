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
async def test_processor_message_handling(message_system):
    """Test basic processor message handling."""
    # Send a processor message
    success = await message_system.send(
        to_agent="processor_agent",
        content="Test processor message",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        from_agent="test_sender",
        metadata={"processor_type": "test"}
    )
    assert success

    # Verify message was received
    messages = await message_system.receive("processor_agent")
    assert len(messages) == 1
    message = messages[0]
    assert message.content == "Test processor message"
    assert message.metadata.get("processor_type") == "test"

@pytest.mark.asyncio
async def test_processor_message_chain(message_system):
    """Test processor message chaining."""
    processed_messages = []
    
    async def processor_handler(message: Message):
        processed_messages.append(message)
        # Simulate processing and send response
        await message_system.send(
            to_agent=message.from_agent,
            content=f"Processed: {message.content}",
            mode=MessageMode.NORMAL,
            priority=message.priority,
            from_agent="processor_agent",
            response_to=message.message_id
        )
    
    # Subscribe to processor messages
    await message_system.subscribe("processor_agent", processor_handler)
    
    # Send a message to be processed
    await message_system.send(
        to_agent="processor_agent",
        content="Test processing chain",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        from_agent="test_sender"
    )
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify original message was processed
    assert len(processed_messages) == 1
    assert processed_messages[0].content == "Test processing chain"
    
    # Verify response was sent
    responses = await message_system.receive("test_sender")
    assert len(responses) == 1
    assert responses[0].content == "Processed: Test processing chain"
    assert responses[0].response_to == processed_messages[0].message_id

@pytest.mark.asyncio
async def test_processor_message_batch(message_system):
    """Test processor batch message handling."""
    processed_messages = []
    
    async def batch_processor(message: Message):
        processed_messages.append(message)
        # Simulate batch processing
        await asyncio.sleep(0.1)
    
    # Subscribe to processor messages
    await message_system.subscribe("processor_agent", batch_processor)
    
    # Send batch of messages
    for i in range(5):
        await message_system.send(
            to_agent="processor_agent",
            content=f"Batch message {i}",
            mode=MessageMode.BULK,
            priority=MessagePriority.NORMAL,
            from_agent="test_sender"
        )
    
    # Wait for batch processing
    await asyncio.sleep(0.6)
    
    # Verify all messages were processed
    assert len(processed_messages) == 5
    for i, message in enumerate(processed_messages):
        assert message.content == f"Batch message {i}"
        assert message.mode == MessageMode.BULK

@pytest.mark.asyncio
async def test_processor_message_priority_handling(message_system):
    """Test processor priority message handling."""
    processed_messages = []
    
    async def priority_processor(message: Message):
        processed_messages.append(message)
        # Simulate processing time based on priority
        await asyncio.sleep(0.1 * (5 - message.priority.value))
    
    # Subscribe to processor messages
    await message_system.subscribe("processor_agent", priority_processor)
    
    # Send messages with different priorities
    priorities = [
        MessagePriority.LOW,
        MessagePriority.NORMAL,
        MessagePriority.HIGH,
        MessagePriority.URGENT,
        MessagePriority.CRITICAL
    ]
    
    for priority in priorities:
        await message_system.send(
            to_agent="processor_agent",
            content=f"Priority {priority.name}",
            mode=MessageMode.PRIORITY,
            priority=priority,
            from_agent="test_sender"
        )
    
    # Wait for processing
    await asyncio.sleep(1.0)
    
    # Verify messages were processed in priority order
    assert len(processed_messages) == 5
    for i, message in enumerate(processed_messages):
        assert message.priority == priorities[4-i]  # Should be processed in reverse priority order 