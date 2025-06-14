"""Mock Discord models for testing."""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

class Activity:
    """Mock Discord Activity for testing."""
    
    def __init__(self, name: str, type: str = "playing"):
        self.name = name
        self.type = type

class MockGuild:
    """Mock Discord Guild for testing (relaxed signature)."""
    
    def __init__(self, id: int = 1, name: str = "Test Guild", **kwargs):  # noqa: D401
        self.id = id
        self.name = name
        self.roles = []
        self.members = []
        self.channels = []
        
    def get_role(self, role_id: int) -> Optional['MockRole']:
        """Get a role by ID."""
        return next((role for role in self.roles if role.id == role_id), None)
        
    def get_member(self, member_id: int) -> Optional['MockMember']:
        """Get a member by ID."""
        return next((member for member in self.members if member.id == member_id), None)
        
    def get_channel(self, channel_id: int) -> Optional['MockChannel']:
        """Get a channel by ID."""
        return next((channel for channel in self.channels if channel.id == channel_id), None)

class MockRole:
    """Mock Discord Role for testing."""
    
    def __init__(self, id: int, name: str, guild: MockGuild):
        self.id = id
        self.name = name
        self.guild = guild
        self.members = []
        
    def add_member(self, member: 'MockMember'):
        """Add a member to this role."""
        if member not in self.members:
            self.members.append(member)
            member.roles.append(self)
            
    def remove_member(self, member: 'MockMember'):
        """Remove a member from this role."""
        if member in self.members:
            self.members.remove(member)
            member.roles = [r for r in member.roles if r.id != self.id]

class MockMember:
    """Mock Discord Member for testing (relaxed signature)."""
    
    def __init__(
        self,
        id: int = 1,
        name: str = "Test User",
        guild: Optional[MockGuild] = None,
        bot: bool = False,
        **kwargs,
    ):  # noqa: D401
        self.id = id
        self.name = name
        self.guild = guild
        self.bot = bot
        self.roles = []
        
    def add_role(self, role: MockRole):
        """Add a role to the member."""
        if role not in self.roles:
            self.roles.append(role)
            role.members.append(self)
        
    def remove_role(self, role: MockRole):
        """Remove a role from the member."""
        if role in self.roles:
            self.roles.remove(role)
            role.members = [m for m in role.members if m.id != self.id]

class MockChannel:
    """Mock Discord Channel for testing (relaxed signature)."""
    
    def __init__(
        self,
        id: int = 1,
        name: str = "test-channel",
        guild: Optional[MockGuild] = None,
        type: str = "text",
        **kwargs,
    ):  # noqa: D401
        self.id = id
        self.name = name
        self.guild = guild
        self.type = type
        self.messages = []
        
    async def send(self, content=None, **kwargs):
        """Mock sending a message to the channel."""
        message = MockMessage(
            id=len(self.messages) + 1,
            content=content,
            channel=self,
            author=self.guild.get_member(1)  # Default to first member
        )
        self.messages.append(message)
        return message

class MockMessage:
    """Mock Discord Message for testing."""
    
    def __init__(
        self,
        id: int | None = None,
        content: str | None = None,
        channel: Optional["MockChannel"] = None,
        author: Optional["MockMember"] = None,
    ) -> None:  # noqa: D401
        self.id = id if id is not None else len(getattr(channel, "messages", [])) + 1 if channel else 0
        self.content = content or ""
        self.channel = channel
        self.author = author or MockMember(id=0, name="Mock Author", guild=None)
        self.embeds = []
        
    async def add_reaction(self, emoji):
        """Mock adding a reaction to the message."""
        pass
        
    async def remove_reaction(self, emoji, member):
        """Mock removing a reaction from the message."""
        pass

class MockEmbed:
    """Mock Discord Embed for testing."""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.color = kwargs.get('color')
        self.fields = []
        self.footer = None
        self.image = None
        self.thumbnail = None
        self.author = None
        self.timestamp = None
        
    def add_field(self, name: str, value: str, inline: bool = False):
        """Add a field to the embed."""
        self.fields.append({
            'name': name,
            'value': value,
            'inline': inline
        })
        
    def set_footer(self, text: str, icon_url: Optional[str] = None):
        """Set the footer of the embed."""
        self.footer = {
            'text': text,
            'icon_url': icon_url
        }
        
    def set_image(self, url: str):
        """Set the image of the embed."""
        self.image = {'url': url}
        
    def set_thumbnail(self, url: str):
        """Set the thumbnail of the embed."""
        self.thumbnail = {'url': url}

class MockFile:
    """Mock Discord File for testing."""
    
    def __init__(self, filename: str, content: Union[str, bytes], description: Optional[str] = None,
                 spoiler: bool = False):
        self.filename = filename
        self.content = content
        self.description = description
        self.spoiler = spoiler

class MockWebhook:
    """Mock Discord Webhook for testing."""
    
    def __init__(self, id: int, token: str, channel: MockChannel):
        self.id = id
        self.token = token
        self.channel = channel
        self.messages = []
        
    async def send(self, content=None, **kwargs):
        """Mock sending a message via webhook."""
        message = MockMessage(
            id=len(self.messages) + 1,
            content=content,
            channel=self.channel,
            author=self.channel.guild.get_member(1)  # Default to first member
        )
        self.messages.append(message)
        return message
        
    async def edit_message(self, message_id: int, **kwargs):
        """Mock editing a webhook message."""
        message = next((m for m in self.messages if m.id == message_id), None)
        if message:
            for key, value in kwargs.items():
                setattr(message, key, value)
        return message
        
    async def delete_message(self, message_id: int):
        """Mock deleting a webhook message."""
        self.messages = [m for m in self.messages if m.id != message_id]

class Embed:
    """Mock Discord Embed class."""
    def __init__(self, title=None, description=None, color=None):
        self.title = title
        self.description = description
        self.color = color
        self.fields = []
        self.footer = None
        self.image = None
        self.thumbnail = None

    def add_field(self, name, value, inline=False):
        """Add a field to the embed."""
        self.fields.append({"name": name, "value": value, "inline": inline})

    def set_footer(self, text, icon_url=None):
        """Set the footer of the embed."""
        self.footer = {"text": text, "icon_url": icon_url}

    def set_image(self, url):
        """Set the image of the embed."""
        self.image = {"url": url}

    def set_thumbnail(self, url):
        """Set the thumbnail of the embed."""
        self.thumbnail = {"url": url}

class ButtonStyle:
    """Mock Discord ButtonStyle class."""
    Primary = 1
    Secondary = 2
    Success = 3
    Danger = 4
    Link = 5

class Interaction:  # noqa: D401
    """Mock Discord Interaction class (relaxed signature)."""

    def __init__(self, **kwargs):  # noqa: D401
        self.id = kwargs.get("id", 1)
        self.type = kwargs.get("type", 2)
        self.data = kwargs.get("data", {})
        self.guild_id = kwargs.get("guild_id")
        self.channel_id = kwargs.get("channel_id")

        self.user = kwargs.get("user")
        self.message = kwargs.get("message")
        self.channel = kwargs.get("channel")
        self.response = None
         
    async def respond(self, content=None, embed=None, ephemeral=False):
        """Mock response to an interaction."""
        self.response = {
            "content": content,
            "embed": embed,
            "ephemeral": ephemeral
        }
        return self.response

    async def followup(self, content=None, embed=None, ephemeral=False):
        """Mock followup to an interaction."""
        return await self.respond(content, embed, ephemeral)

class Color:
    """Mock Discord Color class."""
    
    def __init__(self, value: int):
        self.value = value
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Color):
            return False
        return self.value == other.value
    
    @classmethod
    def default(cls) -> 'Color':
        return cls(0)
    
    @classmethod
    def blue(cls) -> 'Color':
        return cls(0x3498db)
    
    @classmethod
    def dark_blue(cls) -> 'Color':
        return cls(0x206694)
    
    @classmethod
    def green(cls) -> 'Color':
        return cls(0x2ecc71)
    
    @classmethod
    def dark_green(cls) -> 'Color':
        return cls(0x27ae60)
    
    @classmethod
    def red(cls) -> 'Color':
        return cls(0xe74c3c)
    
    @classmethod
    def dark_red(cls) -> 'Color':
        return cls(0xc0392b)
    
    @classmethod
    def gold(cls) -> 'Color':
        return cls(0xf1c40f)
    
    @classmethod
    def dark_gold(cls) -> 'Color':
        return cls(0xf39c12)
    
    @classmethod
    def purple(cls) -> 'Color':
        return cls(0x9b59b6)
    
    @classmethod
    def dark_purple(cls) -> 'Color':
        return cls(0x8e44ad)
    
    @classmethod
    def teal(cls) -> 'Color':
        return cls(0x1abc9c)
    
    @classmethod
    def dark_teal(cls) -> 'Color':
        return cls(0x16a085)
    
    @classmethod
    def orange(cls) -> 'Color':
        return cls(0xe67e22)
    
    @classmethod
    def dark_orange(cls) -> 'Color':
        return cls(0xd35400)
    
    @classmethod
    def grey(cls) -> 'Color':
        return cls(0x95a5a6)
    
    @classmethod
    def dark_grey(cls) -> 'Color':
        return cls(0x7f8c8d)
    
    @classmethod
    def darker_grey(cls) -> 'Color':
        return cls(0x2c2f33)
    
    @classmethod
    def light_grey(cls) -> 'Color':
        return cls(0xbcc0c0)
    
    @classmethod
    def dark_theme(cls) -> 'Color':
        return cls(0x36393f)
    
    @classmethod
    def blurple(cls) -> 'Color':
        return cls(0x7289da)
    
    @classmethod
    def dark_blurple(cls) -> 'Color':
        return cls(0x5865f2)

def create_mock_embed(title: Optional[str] = None, description: Optional[str] = None,
                     color: Optional[int] = None, fields: Optional[List[Dict[str, Any]]] = None,
                     footer: Optional[Dict[str, str]] = None, image: Optional[Dict[str, str]] = None,
                     thumbnail: Optional[Dict[str, str]] = None) -> MockEmbed:
    """Create a mock embed with the given parameters.
    
    Args:
        title: Optional title for the embed
        description: Optional description for the embed
        color: Optional color for the embed
        fields: Optional list of field dictionaries
        footer: Optional footer dictionary
        image: Optional image dictionary
        thumbnail: Optional thumbnail dictionary
        
    Returns:
        A new MockEmbed instance
    """
    embed = MockEmbed(
        title=title,
        description=description,
        color=color
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', False)
            )
            
    if footer:
        embed.set_footer(
            text=footer.get('text', ''),
            icon_url=footer.get('icon_url')
        )
        
    if image:
        embed.set_image(url=image.get('url', ''))
        
    if thumbnail:
        embed.set_thumbnail(url=thumbnail.get('url', ''))
        
    return embed

__all__ = [
    'MockGuild',
    'MockRole',
    'MockMember',
    'MockChannel',
    'MockMessage',
    'MockEmbed',
    'MockWebhook',
    'MockFile',
    'Activity',
    'create_mock_embed',
    'Embed',
    'ButtonStyle',
    'Interaction',
    'Color'
]
