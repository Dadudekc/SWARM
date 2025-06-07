"""
Discord Mocks
-----------
Mock classes and utilities for Discord.py testing.
"""

from .base import (
    Cog,
    Guild,
    Context,
    CommandError,
    Command,
    Color
)

from .models import (
    MockGuild,
    MockMember,
    MockRole,
    MockChannel,
    MockMessage,
    MockEmbed
)

from .client import (
    Client,
    MockCommand,
    MockBot,
    MockCog,
    VoiceClient,
    MockContext
)

from .webhook import (
    MockWebhook,
    MockFile
)

from .commands import (
    Context as CommandContext,
    Command as CommandClass,
    Group,
    Cog as CommandCog,
    commands
)

from .helpers import (
    create_mock_guild,
    create_mock_context,
    create_mock_bot,
    create_mock_embed,
    run_async_test,
    async_test,
    mock_command_decorator
)

from types import SimpleNamespace

# Create a 'discord' attribute that exposes the necessary mock classes
discord = SimpleNamespace(
    Client=Client,
    MockBot=MockBot,
    MockCommand=MockCommand,
    MockCog=MockCog,
    VoiceClient=VoiceClient,
    MockContext=MockContext,
    Cog=Cog,
    Guild=Guild,
    Context=Context,
    CommandError=CommandError,
    Command=Command,
    Color=Color,
    MockGuild=MockGuild,
    MockMember=MockMember,
    MockRole=MockRole,
    MockChannel=MockChannel,
    MockMessage=MockMessage,
    MockEmbed=MockEmbed,
    Webhook=MockWebhook,
    File=MockFile,
    Member=MockMember  # Explicitly add Member
)

# Add a 'ui' attribute to the 'discord' SimpleNamespace
discord.ui = SimpleNamespace()

# Create a 'commands' attribute that exposes the necessary mock command-related classes or functions
commands = SimpleNamespace(
    Context=CommandContext,
    Command=CommandClass,
    Group=Group,
    Cog=CommandCog,
    command=commands.command,
    group=commands.group
)

# Add Member as a top-level export
Member = MockMember

__all__ = [
    # Base classes
    "Cog",
    "Guild",
    "Context",
    "CommandError",
    "Command",
    "Color",
    
    # Models
    "MockGuild",
    "MockMember",
    "MockRole",
    "MockChannel",
    "MockMessage",
    "MockEmbed",
    
    # Client
    "Client",
    "MockCommand",
    "MockBot",
    "MockCog",
    "VoiceClient",
    
    # Webhook
    "MockWebhook",
    "MockFile",
    
    # Commands
    "CommandContext",
    "CommandClass",
    "Group",
    "CommandCog",
    "commands",
    
    # Helpers
    "create_mock_guild",
    "create_mock_context",
    "create_mock_bot",
    "create_mock_embed",
    "run_async_test",
    "async_test",
    "mock_command_decorator",
    
    # Top-level exports
    "Member",
    "discord"
]
