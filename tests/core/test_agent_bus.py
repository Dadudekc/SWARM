import pytest
from datetime import datetime
from dreamos.core.messaging.unified_message_system import MessageSystem
from dreamos.core.messaging.common import Message
from dreamos.core.messaging.enums import MessageMode, MessagePriority, MessageType

@pytest.fixture
def message_system():
    """Create a test message system instance."""
    return MessageSystem()

@pytest.mark.asyncio
async def test_send_message(message_system):
    """Test sending a message through the system."""
    # Send a test message
    success = await message_system.send(
        to_agent="test_agent",
        content="Test message",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        from_agent="test_sender"
    )
    assert success

    # Verify message was received
    messages = await message_system.receive("test_agent")
    assert len(messages) == 1
    message = messages[0]
    assert message.content == "Test message"
    assert message.to_agent == "test_agent"
    assert message.from_agent == "test_sender"
    assert message.mode == MessageMode.NORMAL
    assert message.priority == MessagePriority.NORMAL

@pytest.mark.asyncio
async def test_message_subscription(message_system):
    """Test message subscription functionality."""
    received_messages = []
    
    async def message_handler(message: Message):
        received_messages.append(message)
    
    # Subscribe to messages
    await message_system.subscribe("test_agent", message_handler)
    
    # Send a message
    await message_system.send(
        to_agent="test_agent",
        content="Test subscription",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    
    # Wait for message processing
    await asyncio.sleep(0.1)
    
    # Verify message was received by handler
    assert len(received_messages) == 1
    assert received_messages[0].content == "Test subscription"

@pytest.mark.asyncio
async def test_message_history(message_system):
    """Test message history functionality."""
    # Send multiple messages
    for i in range(3):
        await message_system.send(
            to_agent="test_agent",
            content=f"Test message {i}",
            mode=MessageMode.NORMAL,
            priority=MessagePriority.NORMAL
        )
    
    # Get message history
    history = await message_system.get_history(agent_id="test_agent")
    assert len(history) == 3
    
    # Verify message order
    for i, message in enumerate(history):
        assert message.content == f"Test message {i}"

@pytest.mark.asyncio
async def test_message_acknowledgment(message_system):
    """Test message acknowledgment functionality."""
    # Send a message
    await message_system.send(
        to_agent="test_agent",
        content="Test acknowledgment",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL
    )
    
    # Get the message
    messages = await message_system.receive("test_agent")
    assert len(messages) == 1
    message = messages[0]
    
    # Acknowledge the message
    success = await message_system.acknowledge(message.message_id)
    assert success
    
    # Verify message was removed from queue
    messages = await message_system.receive("test_agent")
    assert len(messages) == 0 
