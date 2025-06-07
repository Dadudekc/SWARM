"""
Mock Discord Module
-----------------
Mock classes and utilities for Discord.py testing.
"""

from .discord import discord
from .models import (
    MockGuild,
    MockMember,
    MockRole,
    MockChannel,
    MockMessage,
    MockEmbed,
    MockContext,
    create_mock_embed
)
from .webhook import MockWebhook, MockFile
from .client import Client, MockBot, MockCog, VoiceClient, MockCommand
from types import SimpleNamespace

# Expose a mock 'commands' namespace
commands = SimpleNamespace(
    Command=MockCommand,
    CommandError=Exception,
    Context=MockContext,
    Cog=MockCog,
    Bot=MockBot
)

__all__ = [
    'discord',
    'commands',
    'Client',
    'MockBot',
    'MockCog',
    'VoiceClient',
    'MockGuild',
    'MockMember',
    'MockRole',
    'MockChannel',
    'MockMessage',
    'MockEmbed',
    'MockContext',
    'MockWebhook',
    'MockFile',
    'MockCommand',
    'create_mock_embed'
] 