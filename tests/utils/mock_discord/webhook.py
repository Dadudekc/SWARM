"""
Discord Webhook Mocks
-------------------
Mock webhook classes for Discord.py testing.
"""

from typing import Optional, BinaryIO
from dataclasses import dataclass
from .models import MockMessage, MockChannel, MockMember

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

@dataclass
class MockFile:
    """Mock Discord file."""
    filename: str
    fp: BinaryIO
    description: Optional[str] = None
    spoiler: bool = False
    
    def __post_init__(self):
        """Initialize file attributes."""
        self.fp.seek(0)
        self.content = self.fp.read()
        self.fp.seek(0)
    
    def close(self):
        """Close the file."""
        self.fp.close()

__all__ = [
    'MockWebhook',
    'MockFile'
] 