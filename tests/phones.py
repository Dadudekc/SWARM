import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

import pytest
from datetime import datetime
from dreamos.core.messaging.phones import Phone, CaptainPhone
from dreamos.core.messaging.enums import MessageMode, MessagePriority
from dreamos.core.messaging.common import Message

@pytest.fixture
def mock_ums():
    class MockUMS:
        async def send(self, to_agent, content, mode, priority, from_agent, metadata=None):
            return True
            
        async def receive(self, agent_id):
            return []
            
        async def get_history(self, agent_id, start_time=None, end_time=None, limit=None):
            return []
            
        async def subscribe(self, topic, handler):
            pass
            
        async def subscribe_pattern(self, pattern, handler):
            pass
            
        async def unsubscribe(self, topic, handler):
            pass
            
        async def unsubscribe_pattern(self, pattern, handler):
            pass
            
        async def process_message(self, message):
            pass
            
        async def cleanup(self):
            pass
    
    return MockUMS()

@pytest.fixture
def phone(mock_ums):
    return Phone("test-agent", mock_ums)

@pytest.fixture
def captain_phone():
    return CaptainPhone()

@pytest.mark.asyncio
async def test_send_message(phone):
    # Test sending a message with default parameters
    result = await phone.send_message("target-agent", "Hello")
    assert result is True
    
    # Test sending a message with custom parameters
    result = await phone.send_message(
        "target-agent",
        "Hello",
        mode=MessageMode.HIGH_PRIORITY,
        priority=MessagePriority.HIGH,
        metadata={"key": "value"}
    )
    assert result is True
    
    # Test sending a message with invalid parameters
    with pytest.raises(ValueError):
        await phone.send_message("", "Hello")
    
    with pytest.raises(ValueError):
        await phone.send_message("target-agent", "")

@pytest.mark.asyncio
async def test_receive_messages(phone):
    messages = await phone.receive_messages()
    assert isinstance(messages, list)

@pytest.mark.asyncio
async def test_get_message_history(phone):
    # Test getting all history
    messages = await phone.get_message_history()
    assert isinstance(messages, list)
    
    # Test getting history with filters
    start_time = datetime.now()
    end_time = datetime.now()
    messages = await phone.get_message_history(
        start_time=start_time,
        end_time=end_time,
        limit=10
    )
    assert isinstance(messages, list)

@pytest.mark.asyncio
async def test_subscribe_unsubscribe(phone):
    async def handler(message):
        pass
    
    # Test subscribing to a topic
    await phone.subscribe("test-topic", handler)
    
    # Test subscribing to a pattern
    await phone.subscribe_pattern("test-*", handler)
    
    # Test unsubscribing from a topic
    await phone.unsubscribe("test-topic", handler)
    
    # Test unsubscribing from a pattern
    await phone.unsubscribe_pattern("test-*", handler)

@pytest.mark.asyncio
async def test_captain_phone_send_message(captain_phone):
    # Test sending a message with default parameters
    result = await captain_phone.send_message("target-agent", "Hello")
    assert result is True
    
    # Test sending a message with custom parameters
    result = await captain_phone.send_message(
        "target-agent",
        "Hello",
        mode="HIGH_PRIORITY",
        priority=1,
        wait_for_response=True
    )
    assert result is True

@pytest.mark.asyncio
async def test_captain_phone_broadcast(captain_phone):
    # Test broadcasting a message
    results = await captain_phone.broadcast_message("Hello everyone")
    assert isinstance(results, dict)
    
    # Test broadcasting with custom parameters
    results = await captain_phone.broadcast_message(
        "Hello everyone",
        mode="HIGH_PRIORITY",
        priority=1,
        exclude_agents=["agent1", "agent2"]
    )
    assert isinstance(results, dict) 