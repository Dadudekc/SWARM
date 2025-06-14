# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from . import base
from . import client
from . import commands
from . import discord
from . import helpers
from . import interaction
from . import models
from . import ui
from . import voice
from . import webhook

__all__ = [
    'base',
    'client',
    'commands',
    'discord',
    'helpers',
    'interaction',
    'models',
    'ui',
    'voice',
    'webhook',
]

# Inject basic mock classes from the standalone implementation if available.
try:
    from ..mock_discord import *  # type: ignore  # noqa: F401,F403
except ImportError:  # pragma: no cover
    pass

__all__.extend([
    'Guild',
    'Member',
    'TextChannel',
    'Message',
    'Interaction',
    'Context',
    'Embed',
])

# ---------------------------------------------------------------------------
# Export common mock classes at package root for convenience (legacy tests
# expect e.g. `from tests.utils.mock_discord import Guild`).
# ---------------------------------------------------------------------------
from .models import (  # noqa: F401
    MockGuild as Guild,
    MockMember as Member,
    MockChannel as TextChannel,
    MockMessage as Message,
    MockEmbed as Embed,
)

from .interaction import (  # noqa: F401
    Interaction,
    InteractionResponse,
    InteractionFollowup,
)

from .client import MockContext as Context  # noqa: F401

# Optional discord.py-style Intents placeholder

class Intents:  # noqa: D401
    """Minimal stub for `discord.Intents`."""

    @classmethod
    def all(cls):  # noqa: D401
        return cls()


__all__.extend([
    'Guild',
    'Member',
    'TextChannel',
    'Message',
    'Interaction',
    'Context',
    'Embed',
    'InteractionResponse',
    'InteractionFollowup',
    'Intents',
])

# ---------------------------------------------------------------------------
# Exceptions mirroring discord.ext.commands errors --------------------------
# ---------------------------------------------------------------------------


class CommandError(Exception):  # noqa: D401
    """Base command error stub."""


class CommandNotFound(CommandError):
    pass


class MissingRequiredArgument(CommandError):
    pass


class BadArgument(CommandError):
    pass


# Re-export command utilities
from .commands import commands  # noqa: F401

# Provide an `ext` namespace to mirror `discord.ext`
import types as _types

_ext = _types.ModuleType('discord.ext')
_ext.commands = commands  # type: ignore[attr-defined]

import sys as _sys
_sys.modules['discord.ext'] = _ext
ext = _ext

__all__.extend([
    'CommandError',
    'CommandNotFound',
    'MissingRequiredArgument',
    'BadArgument',
    'commands',
    'ext',
])

from .commands import Command, Bot  # noqa: F401

__all__.extend([
    'Command',
    'Bot',
])

# ---------------------------------------------------------------------------
# VoiceClient stub (legacy voice interface)
# ---------------------------------------------------------------------------


class VoiceClient:  # noqa: D401
    async def connect(self, *args, **kwargs):  # noqa: D401
        return True

    async def disconnect(self):  # noqa: D401
        return True


__all__.append('VoiceClient')

# Gateway placeholder --------------------------------------------------------


class Gateway:  # noqa: D401
    async def send(self, *args, **kwargs):  # noqa: D401
        return True


__all__.append('Gateway')

# Opus stub (codec interface)


class Opus:  # noqa: D401
    @staticmethod
    def load_opus(*args, **kwargs):  # noqa: D401
        return True


__all__.append('Opus')

# OpusLoader stub -----------------------------------------------------------


class OpusLoader:  # noqa: D401
    @staticmethod
    def load(*args, **kwargs):  # noqa: D401
        return True


__all__.append('OpusLoader')

# ---------------------------------------------------------------------------
# Voice-related classes re-export -------------------------------------------
# The test-suite expects many discord voice helpers directly at the package
# root. Import them lazily from the dedicated ``voice`` submodule if present.
# ---------------------------------------------------------------------------
try:
    from .voice import (
        VoiceState, VoiceProtocol, VoiceRegion,
        VoiceRecv, VoiceSend, VoiceUtils,
        VoiceWebSocket, VoiceWebSocketClient, VoiceWebSocketServer,
        VoiceWebSocketUtils, VoiceWebSocketVoice,
        VoiceWebSocketVoiceClient, VoiceWebSocketVoiceServer,
        VoiceWebSocketVoiceUtils, VoiceWebSocketVoiceWebSocket,
        VoiceWebSocketVoiceWebSocketClient, VoiceWebSocketVoiceWebSocketServer,
        VoiceWebSocketVoiceWebSocketUtils,
    )  # type: ignore[F401]

    __all__.extend([
        'VoiceState', 'VoiceProtocol', 'VoiceRegion', 'VoiceRecv', 'VoiceSend',
        'VoiceUtils', 'VoiceWebSocket', 'VoiceWebSocketClient', 'VoiceWebSocketServer',
        'VoiceWebSocketUtils', 'VoiceWebSocketVoice', 'VoiceWebSocketVoiceClient',
        'VoiceWebSocketVoiceServer', 'VoiceWebSocketVoiceUtils', 'VoiceWebSocketVoiceWebSocket',
        'VoiceWebSocketVoiceWebSocketClient', 'VoiceWebSocketVoiceWebSocketServer',
        'VoiceWebSocketVoiceWebSocketUtils',
    ])
except ImportError:  # pragma: no cover
    pass
