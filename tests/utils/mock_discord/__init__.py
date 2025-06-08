# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from . import base
from . import client
from . import commands
from . import discord
from . import helpers
from . import models
from . import webhook
from . import ui
from . import voice
from .models import (
    MockGuild, MockRole, MockChannel, MockMember, MockMessage, MockEmbed, MockWebhook, MockFile, Activity, create_mock_embed,
    Embed, ButtonStyle, Color, Interaction
)
from .ui import View, Button, Select, TextInput
from .client import Client, ClientUser, VoiceClient
from .commands import Command, Group
from .voice import (
    Gateway,
    Opus,
    OpusLoader,
    VoiceState,
    VoiceProtocol,
    VoiceRegion,
    VoiceRecv,
    VoiceSend,
    VoiceUtils,
    VoiceWebSocket,
    VoiceWebSocketClient,
    VoiceWebSocketServer,
    VoiceWebSocketUtils,
    VoiceWebSocketVoice,
    VoiceWebSocketVoiceClient,
    VoiceWebSocketVoiceServer,
    VoiceWebSocketVoiceUtils,
    VoiceWebSocketVoiceWebSocket,
    VoiceWebSocketVoiceWebSocketClient,
    VoiceWebSocketVoiceWebSocketServer,
    VoiceWebSocketVoiceWebSocketUtils,
)
from .discord import Intents
from .webhook import Webhook
from enum import Enum
from typing import Any

# Alias MockEmbed as Embed for compatibility
Embed = MockEmbed

class ButtonStyle(Enum):
    """Mock Discord button styles."""
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5

class Color:
    """Mock Discord color class."""
    def __init__(self, value: int):
        self.value = value
        
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> 'Color':
        """Create a color from RGB values."""
        return cls((r << 16) + (g << 8) + b)
        
    @classmethod
    def from_str(cls, color_str: str) -> 'Color':
        """Create a color from a hex string."""
        if color_str.startswith('#'):
            color_str = color_str[1:]
        return cls(int(color_str, 16))
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
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

class Interaction:
    """Mock Discord Interaction class."""
    
    def __init__(self, message: Any = None):
        self.message = message
        self.response = InteractionResponse(self)
        self.followup = InteractionFollowup(self)
        
    async def respond(self, *args, **kwargs):
        """Respond to the interaction."""
        return await self.response.send_message(*args, **kwargs)
        
    async def edit_original_response(self, *args, **kwargs):
        """Edit the original response."""
        return await self.response.edit_message(*args, **kwargs)
        
    async def delete_original_response(self):
        """Delete the original response."""
        return await self.response.delete_message()

class InteractionResponse:
    """Mock Discord InteractionResponse class."""
    
    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        
    async def send_message(self, *args, **kwargs):
        """Send a message response."""
        return self.interaction.message
        
    async def edit_message(self, *args, **kwargs):
        """Edit the message response."""
        return self.interaction.message
        
    async def delete_message(self):
        """Delete the message response."""
        pass

class InteractionFollowup:
    """Mock Discord InteractionFollowup class."""
    
    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        
    async def send(self, *args, **kwargs):
        """Send a followup message."""
        return self.interaction.message

class Intents:
    """Mock Discord Intents class."""
    
    def __init__(self):
        self.guilds = False
        self.members = False
        self.bans = False
        self.emojis = False
        self.integrations = False
        self.webhooks = False
        self.invites = False
        self.voice_states = False
        self.presences = False
        self.messages = False
        self.guild_messages = False
        self.dm_messages = False
        self.reactions = False
        self.guild_reactions = False
        self.dm_reactions = False
        self.typing = False
        self.guild_typing = False
        self.dm_typing = False
    
    @classmethod
    def default(cls):
        """Create default intents."""
        return cls()
    
    @classmethod
    def all(cls):
        """Create all intents."""
        intents = cls()
        for attr in dir(intents):
            if not attr.startswith('_'):
                setattr(intents, attr, True)
        return intents

__all__ = [
    'base',
    'client',
    'commands',
    'discord',
    'helpers',
    'models',
    'webhook',
    'ui',
    'voice',
    'MockGuild',
    'MockRole',
    'MockChannel',
    'MockMember',
    'MockMessage',
    'MockEmbed',
    'MockWebhook',
    'MockFile',
    'Activity',
    'create_mock_embed',
    'Client',
    'ClientUser',
    'Command',
    'Group',
    'Intents',
    'View',
    'Button',
    'Select',
    'TextInput',
    'VoiceClient',
    'Gateway',
    'Opus',
    'OpusLoader',
    'VoiceState',
    'VoiceProtocol',
    'VoiceRegion',
    'VoiceRecv',
    'VoiceSend',
    'VoiceUtils',
    'VoiceWebSocket',
    'VoiceWebSocketClient',
    'VoiceWebSocketServer',
    'VoiceWebSocketUtils',
    'VoiceWebSocketVoice',
    'VoiceWebSocketVoiceClient',
    'VoiceWebSocketVoiceServer',
    'VoiceWebSocketVoiceUtils',
    'VoiceWebSocketVoiceWebSocket',
    'VoiceWebSocketVoiceWebSocketClient',
    'VoiceWebSocketVoiceWebSocketServer',
    'VoiceWebSocketVoiceWebSocketUtils',
    'Webhook',
    'ButtonStyle',
    'Color',
    'Interaction',
    'InteractionResponse',
    'InteractionFollowup',
]
