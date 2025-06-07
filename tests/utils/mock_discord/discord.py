"""
Discord Mock Module
-----------------
Mock module that re-exports all mock Discord classes.
"""

import sys
from types import SimpleNamespace
from .models import (
    MockGuild,
    MockMember,
    MockRole,
    MockChannel,
    MockMessage,
    MockEmbed
)
from .webhook import MockWebhook, MockFile
from .client import Client, MockCommand
import types

# Create a module-like object for discord
discord = types.ModuleType('discord')

# Attach all mocks as attributes
discord.Guild = MockGuild
discord.Member = MockMember
discord.Role = MockRole
discord.Channel = MockChannel
discord.Message = MockMessage
discord.Embed = MockEmbed
discord.Webhook = MockWebhook
discord.File = MockFile
discord.Client = Client
discord.Command = MockCommand

discord.Color = SimpleNamespace(
    blue=0x3498db,
    red=0xe74c3c,
    green=0x2ecc71,
    gold=0xf1c40f,
    purple=0x9b59b6,
    teal=0x1abc9c,
    orange=0xe67e22,
    pink=0xe91e63,
    black=0x000000,
    white=0xffffff
)
discord.Status = SimpleNamespace(
    online="online",
    idle="idle",
    dnd="dnd",
    offline="offline"
)
discord.ChannelType = SimpleNamespace(
    text=0,
    voice=2,
    category=4,
    news=5,
    store=6
)

# Make the discord module available in sys.modules
sys.modules['discord'] = discord

__all__ = [
    'discord',
    'MockGuild',
    'MockMember',
    'MockRole',
    'MockChannel',
    'MockMessage',
    'MockEmbed',
    'MockWebhook',
    'MockFile'
] 