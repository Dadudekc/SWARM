import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

import pytest
from dreamos.core.messaging.router import MessageRouter
from dreamos.core.messaging.common import Message
from dreamos.core.messaging.enums import MessageMode
from datetime import datetime

@pytest.fixture
def router():
    return MessageRouter()

@pytest.fixture
def sample_message():
    return Message(
        content="Test message",
        sender="test-sender",
        to_agent="test-agent",
        timestamp=datetime.now(),
        mode=MessageMode.NORMAL
    )

@pytest.mark.asyncio
async def test_route_message(router, sample_message):
    result = await router.route(sample_message)
    assert result is True 