"""
Discord Webhook Mocks
-------------------
Mock webhook classes for Discord.py testing.
"""

from typing import Optional, BinaryIO, Union
from dataclasses import dataclass
from io import BytesIO
from .models import MockMessage, MockChannel, MockMember, MockFile

@dataclass
class MockWebhook:
    """Mock Discord webhook."""
    id: int
    token: str
    url: str
    channel_id: int
    guild_id: Optional[int] = None
    name: Optional[str] = None
    
    async def send(self, content: Optional[str] = None, **kwargs) -> MockMessage:
        """Send a message through the webhook."""
        return MockMessage(
            id=1,
            content=content or "",
            channel=MockChannel(id=self.channel_id, name="webhook-channel"),
            author=MockMember(id=self.id, name=self.name or "Webhook")
        )

__all__ = [
    'MockWebhook',
    'MockFile'
] 