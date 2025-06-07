"""Mock Discord models for testing."""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

class MockGuild:
    """Mock Discord Guild for testing."""
    
    def __init__(self, id: int, name: str):
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
    """Mock Discord Member for testing."""
    
    def __init__(self, id: int, name: str, guild: MockGuild, bot: bool = False):
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
    """Mock Discord Channel for testing."""
    
    def __init__(self, id: int, name: str, guild: MockGuild, type: str = "text"):
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
    
    def __init__(self, id: int, content: str, channel: MockChannel, author: MockMember):
        self.id = id
        self.content = content
        self.channel = channel
        self.author = author
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

__all__ = [
    'MockGuild',
    'MockRole',
    'MockMember',
    'MockChannel',
    'MockMessage',
    'MockEmbed',
    'MockWebhook',
    'MockFile'
]
