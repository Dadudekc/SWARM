"""
Discord Mock Module
-----------------
Mock module that re-exports all mock Discord classes.
"""

import sys
from types import SimpleNamespace
from enum import Enum, auto
from typing import Optional, Any, List, Dict, Union

from .models import (
    MockGuild,
    MockMember,
    MockRole,
    MockChannel,
    MockMessage,
    MockEmbed
)
from .webhook import MockWebhook, MockFile
from .client import Client, ClientUser
from .base import Color
import types
from .ui import View, Button, Select, TextInput, Modal, ButtonStyle

class Status(str, Enum):
    """Mock Status enum."""
    online = "online"
    idle = "idle"
    dnd = "dnd"
    offline = "offline"

class ChannelType(int, Enum):
    """Mock ChannelType enum."""
    text = 0
    voice = 2
    category = 4
    news = 5
    store = 6

class ActivityType(Enum):
    """Mock activity types."""
    playing = auto()
    streaming = auto()
    listening = auto()
    watching = auto()
    custom = auto()
    competing = auto()

class Activity:
    """Mock Activity class."""
    def __init__(self, name, type=ActivityType.playing, **kwargs):
        self.name = name
        self.type = type
        self.url = kwargs.get('url')
        self.details = kwargs.get('details')
        self.state = kwargs.get('state')

class Intents:
    """Mock Intents class."""
    def __init__(self, **kwargs):
        self.guilds = kwargs.get('guilds', False)
        self.members = kwargs.get('members', False)
        self.bans = kwargs.get('bans', False)
        self.emojis = kwargs.get('emojis', False)
        self.integrations = kwargs.get('integrations', False)
        self.webhooks = kwargs.get('webhooks', False)
        self.invites = kwargs.get('invites', False)
        self.voice_states = kwargs.get('voice_states', False)
        self.presences = kwargs.get('presences', False)
        self.messages = kwargs.get('messages', False)
        self.guild_messages = kwargs.get('guild_messages', False)
        self.dm_messages = kwargs.get('dm_messages', False)
        self.reactions = kwargs.get('reactions', False)
        self.guild_reactions = kwargs.get('guild_reactions', False)
        self.dm_reactions = kwargs.get('dm_reactions', False)
        self.typing = kwargs.get('typing', False)
        self.guild_typing = kwargs.get('guild_typing', False)
        self.dm_typing = kwargs.get('dm_typing', False)

    @classmethod
    def default(cls):
        """Create default intents."""
        return cls(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            integrations=True,
            webhooks=True,
            invites=True,
            voice_states=True,
            presences=True,
            messages=True,
            guild_messages=True,
            dm_messages=True,
            reactions=True,
            guild_reactions=True,
            dm_reactions=True,
            typing=True,
            guild_typing=True,
            dm_typing=True
        )

    @classmethod
    def all(cls):
        """Create all intents."""
        return cls.default()

class Color:
    """Mock Discord color class."""
    def __init__(self, value: int):
        self.value = value
    
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> 'Color':
        """Create color from RGB values."""
        return cls((r << 16) + (g << 8) + b)
    
    @classmethod
    def from_str(cls, color_str: str) -> 'Color':
        """Create color from hex string."""
        return cls(int(color_str.lstrip('#'), 16))

# Create color instances
Color.blue = Color.from_rgb(0, 0, 255)
Color.red = Color.from_rgb(255, 0, 0)
Color.green = Color.from_rgb(0, 255, 0)
Color.yellow = Color.from_rgb(255, 255, 0)
Color.purple = Color.from_rgb(128, 0, 128)
Color.orange = Color.from_rgb(255, 165, 0)
Color.teal = Color.from_rgb(0, 128, 128)
Color.white = Color.from_rgb(255, 255, 255)
Color.black = Color.from_rgb(0, 0, 0)
Color.grey = Color.from_rgb(128, 128, 128)
Color.dark_grey = Color.from_rgb(64, 64, 64)
Color.light_grey = Color.from_rgb(192, 192, 192)

# Create a module-like object for discord
discord = SimpleNamespace(
    Client=Client,
    ClientUser=ClientUser,
    Guild=MockGuild,
    Member=MockMember,  # Explicitly set Member
    Role=MockRole,
    Channel=MockChannel,
    Message=MockMessage,
    Embed=MockEmbed,
    Webhook=MockWebhook,
    File=MockFile,
    Color=Color,
    ActivityType=ActivityType,
    Activity=Activity,
    Intents=Intents,
    ui=SimpleNamespace(
        View=View,
        Button=Button,
        Select=Select,
        TextInput=TextInput,
        Modal=Modal,
        ButtonStyle=ButtonStyle
    )
)

# Add Member as a top-level export
Member = MockMember

# Attach all mocks as attributes
discord.Status = Status
discord.ChannelType = ChannelType
discord.ActivityType = ActivityType
discord.Activity = Activity
discord.Intents = Intents

# Make the discord module available in sys.modules
sys.modules['discord'] = discord

# Add Guild as an alias for MockGuild
Guild = MockGuild
# Add Member, Role, Channel, Message, Embed, Webhook, File, Client, ClientUser as aliases
Role = MockRole
Channel = MockChannel
Message = MockMessage
Embed = MockEmbed
Webhook = MockWebhook
File = MockFile
Client = Client
ClientUser = ClientUser

__all__ = [
    'discord',
    'Guild',
    'MockGuild',
    'MockMember',
    'Member',  # Ensure Member is in __all__
    'MockRole',
    'MockChannel',
    'MockMessage',
    'MockEmbed',
    'MockWebhook',
    'MockFile',
    'Client',
    'ClientUser',
    'Color',
    'Status',
    'ChannelType',
    'ActivityType',
    'Activity',
    'Intents'
] 