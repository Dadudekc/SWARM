"""
Discord Mock Module
-----------------
Mock module that re-exports all mock Discord classes.
"""

import sys
from types import SimpleNamespace
from enum import Enum
from typing import Optional, Any, List, Dict

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

class ActivityType(int, Enum):
    """Mock ActivityType enum."""
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

class Activity:
    """Mock Activity class."""
    def __init__(self, name, type=ActivityType.playing, **kwargs):
        self.name = name
        self.type = type
        self.url = kwargs.get('url')
        self.details = kwargs.get('details')
        self.state = kwargs.get('state')

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
    Color=Color
)

# Add Member as a top-level export
Member = MockMember

# Attach all mocks as attributes
discord.Status = Status
discord.ChannelType = ChannelType
discord.ActivityType = ActivityType
discord.Activity = Activity

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
    'Activity'
] 