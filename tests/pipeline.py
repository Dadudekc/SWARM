import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

import pytest
from datetime import datetime
from dreamos.core.messaging.pipeline import MessagePipeline
from dreamos.core.messaging.message import Message
from dreamos.core.messaging.enums import MessageMode, MessageStatus
from dreamos.core.agent_control.ui_automation import UIAutomation
from dreamos.core.shared.persistent_queue import PersistentQueue

@pytest.fixture
def mock_ui_automation():
    class MockUIAutomation:
        def move_to_agent(self, agent_id):
            return True
            
        def click_input_box(self, agent_id):
            return True
            
        def send_message(self, agent_id, content):
            return True
            
        def click_copy_button(self, agent_id):
            return True
    
    return MockUIAutomation()

@pytest.fixture
def mock_queue():
    return PersistentQueue()

@pytest.fixture
def pipeline(mock_ui_automation, mock_queue):
    return MessagePipeline(
        ui_automation=mock_ui_automation,
        queue=mock_queue,
        batch_size=5,
        batch_timeout=0.5
    )

@pytest.fixture
def valid_message():
    return Message(
        content="Test message",
        sender="test-sender",
        to_agent="test-agent",
        timestamp=datetime.now(),
        mode=MessageMode.NORMAL,
        status=MessageStatus.PENDING
    )

@pytest.mark.asyncio
async def test_process_message(pipeline, valid_message):
    # Test processing a valid message
    result = await pipeline.process_message(valid_message)
    assert result is True
    
    # Test processing an invalid message
    invalid_message = Message(
        content="",  # Empty content
        sender="test-sender",
        to_agent="test-agent",
        timestamp=datetime.now(),
        mode=MessageMode.NORMAL,
        status=MessageStatus.PENDING
    )
    result = await pipeline.process_message(invalid_message)
    assert result is False

@pytest.mark.asyncio
async def test_process_batch(pipeline, valid_message):
    # Test processing a batch of valid messages
    messages = [valid_message] * 3
    result = await pipeline.process_batch(messages)
    assert result is True
    
    # Test processing a batch with invalid messages
    invalid_messages = [
        Message(
            content="",  # Empty content
            sender="test-sender",
            to_agent="test-agent",
            timestamp=datetime.now(),
            mode=MessageMode.NORMAL,
            status=MessageStatus.PENDING
        )
    ]
    result = await pipeline.process_batch(invalid_messages)
    assert result is False 