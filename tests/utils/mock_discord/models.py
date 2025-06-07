"""
Discord Model Mocks
-----------------
Mock models for Discord.py testing.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MockContext:
    """Mock Discord command context."""
    message: 'MockMessage'
    channel: 'MockChannel'
    author: 'MockMember'
    guild: Optional['MockGuild'] = None
    bot: Optional[Any] = None
    prefix: str = "!"
    command: Optional[Any] = None
    invoked_with: Optional[str] = None
    invoked_subcommand: Optional[Any] = None
    subcommand_passed: Optional[str] = None
    command_failed: bool = False
    
    async def send(self, content: Optional[str] = None, **kwargs) -> 'MockMessage':
        """Send a message to the channel."""
        return await self.channel.send(content, **kwargs)
    
    async def reply(self, content: Optional[str] = None, **kwargs) -> 'MockMessage':
        """Reply to the message."""
        return await self.channel.send(content, **kwargs)
    
    async def trigger_typing(self) -> None:
        """Trigger typing indicator."""
        pass

@dataclass
class MockGuild:
    """Mock Discord guild."""
    id: int
    name: str
    channels: List['MockChannel'] = field(default_factory=list)
    members: List['MockMember'] = field(default_factory=list)
    roles: List['MockRole'] = field(default_factory=list)
    
    def get_channel(self, channel_id: int) -> Optional['MockChannel']:
        """Get a channel by ID."""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None
    
    def get_member(self, member_id: int) -> Optional['MockMember']:
        """Get a member by ID."""
        for member in self.members:
            if member.id == member_id:
                return member
        return None

@dataclass
class MockMember:
    """Mock Discord member."""
    id: int
    name: str
    display_name: Optional[str] = None
    bot: bool = False
    
    @property
    def mention(self) -> str:
        """Get the member's mention string."""
        return f"<@{self.id}>"

@dataclass
class MockRole:
    """Mock Discord role."""
    id: int
    name: str
    guild: Optional[MockGuild] = None
    color: int = 0

@dataclass
class MockChannel:
    """Mock Discord channel."""
    id: int
    name: str
    guild: Optional[MockGuild] = None
    type: str = "text"
    position: int = 0
    
    async def send(self, content: Optional[str] = None, **kwargs) -> 'MockMessage':
        """Send a message to the channel."""
        return MockMessage(
            id=1,
            content=content or "",
            channel=self,
            author=MockMember(id=1, name="Bot")
        )

@dataclass
class MockMessage:
    """Mock Discord message."""
    id: int
    content: str
    channel: MockChannel
    author: MockMember
    created_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    embeds: List[Dict[str, Any]] = field(default_factory=list)
    
    async def edit(self, **kwargs) -> None:
        """Edit the message."""
        if "content" in kwargs:
            self.content = kwargs["content"]
        self.edited_at = datetime.now()

@dataclass
class MockEmbed:
    """Mock Discord embed."""
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[int] = None
    url: Optional[str] = None
    fields: List[Dict[str, Any]] = field(default_factory=list)
    footer: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    thumbnail: Optional[Dict[str, str]] = None
    author: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None
    
    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        """Add a field to the embed."""
        self.fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })
    
    def set_footer(self, text: str, icon_url: Optional[str] = None) -> None:
        """Set the embed footer."""
        self.footer = {"text": text, "icon_url": icon_url}
    
    def set_image(self, url: str) -> None:
        """Set the embed image."""
        self.image = {"url": url}
    
    def set_thumbnail(self, url: str) -> None:
        """Set the embed thumbnail."""
        self.thumbnail = {"url": url}
    
    def set_author(self, name: str, icon_url: Optional[str] = None) -> None:
        """Set the embed author."""
        self.author = {"name": name, "icon_url": icon_url}

def create_mock_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[int] = None,
    url: Optional[str] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[Dict[str, str]] = None,
    image: Optional[Dict[str, str]] = None,
    thumbnail: Optional[Dict[str, str]] = None,
    author: Optional[Dict[str, str]] = None,
    timestamp: Optional[datetime] = None
) -> MockEmbed:
    """Create a mock Discord embed.
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        url: Embed URL
        fields: List of field dictionaries
        footer: Footer dictionary
        image: Image dictionary
        thumbnail: Thumbnail dictionary
        author: Author dictionary
        timestamp: Embed timestamp
        
    Returns:
        MockEmbed instance
    """
    embed = MockEmbed(
        title=title,
        description=description,
        color=color,
        url=url,
        footer=footer,
        image=image,
        thumbnail=thumbnail,
        author=author,
        timestamp=timestamp
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
    
    return embed 