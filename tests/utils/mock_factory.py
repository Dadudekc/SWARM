"""Factory for creating mock Discord objects for testing."""

from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, field
from types import SimpleNamespace

T = TypeVar('T')

class MockFactory(Generic[T]):
    """Base factory for creating mock objects."""
    
    def __init__(self, default_id: int = 123456789):
        self.default_id = default_id
        self._instances: Dict[int, T] = {}
    
    def create(self, **kwargs) -> T:
        """Create a new mock instance."""
        raise NotImplementedError
    
    def get(self, id: int) -> Optional[T]:
        """Get an existing mock instance by ID."""
        return self._instances.get(id)
    
    def clear(self) -> None:
        """Clear all mock instances."""
        self._instances.clear()

class DiscordMockFactory:
    """Factory for creating Discord-related mock objects."""
    
    def __init__(self):
        self.guilds = MockFactory[Guild]()
        self.members = MockFactory[Member]()
        self.channels = MockFactory[TextChannel]()
        self.messages = MockFactory[Message]()
        self.interactions = MockFactory[Interaction]()
    
    def create_guild(self, **kwargs) -> Guild:
        """Create a mock guild."""
        guild = Guild(**kwargs)
        self.guilds._instances[guild.id] = guild
        return guild
    
    def create_member(self, **kwargs) -> Member:
        """Create a mock member."""
        member = Member(**kwargs)
        self.members._instances[member.id] = member
        return member
    
    def create_channel(self, **kwargs) -> TextChannel:
        """Create a mock channel."""
        channel = TextChannel(**kwargs)
        self.channels._instances[channel.id] = channel
        return channel
    
    def create_message(self, **kwargs) -> Message:
        """Create a mock message."""
        message = Message(**kwargs)
        self.messages._instances[message.id] = message
        return message
    
    def create_interaction(self, **kwargs) -> Interaction:
        """Create a mock interaction."""
        interaction = Interaction(**kwargs)
        self.interactions._instances[interaction.id] = interaction
        return interaction
    
    def create_context(self, **kwargs) -> Context:
        """Create a mock context."""
        return Context(**kwargs)
    
    def create_embed(self, **kwargs) -> Embed:
        """Create a mock embed."""
        return Embed(**kwargs)
    
    def clear_all(self) -> None:
        """Clear all mock instances."""
        self.guilds.clear()
        self.members.clear()
        self.channels.clear()
        self.messages.clear()
        self.interactions.clear()

# Re-export the mock classes
from .mock_discord import (
    Guild, Member, TextChannel, Message, Interaction,
    InteractionResponse, InteractionFollowup, Context, Embed,
    CommandError, CommandNotFound, MissingRequiredArgument,
    BadArgument, Command, Bot, commands, ext,
    VoiceClient, Gateway, Opus, OpusLoader,
    VoiceState, VoiceProtocol, VoiceRegion, VoiceRecv,
    VoiceSend, VoiceUtils, VoiceWebSocket, VoiceWebSocketClient,
    VoiceWebSocketServer, VoiceWebSocketUtils, VoiceWebSocketVoice,
    VoiceWebSocketVoiceClient, VoiceWebSocketVoiceServer,
    VoiceWebSocketVoiceUtils, VoiceWebSocketVoiceWebSocket,
    VoiceWebSocketVoiceWebSocketClient, VoiceWebSocketVoiceWebSocketServer,
    VoiceWebSocketVoiceWebSocketUtils, Intents
)

# Create a singleton instance
mock_factory = DiscordMockFactory()

# Convenience functions
def create_mock_guild(**kwargs) -> Guild:
    """Create a mock guild."""
    return mock_factory.create_guild(**kwargs)

def create_mock_member(**kwargs) -> Member:
    """Create a mock member."""
    return mock_factory.create_member(**kwargs)

def create_mock_channel(**kwargs) -> TextChannel:
    """Create a mock channel."""
    return mock_factory.create_channel(**kwargs)

def create_mock_message(**kwargs) -> Message:
    """Create a mock message."""
    return mock_factory.create_message(**kwargs)

def create_mock_interaction(**kwargs) -> Interaction:
    """Create a mock interaction."""
    return mock_factory.create_interaction(**kwargs)

def create_mock_context(**kwargs) -> Context:
    """Create a mock context."""
    return mock_factory.create_context(**kwargs)

def create_mock_embed(**kwargs) -> Embed:
    """Create a mock embed."""
    return mock_factory.create_embed(**kwargs)

def clear_all_mocks() -> None:
    """Clear all mock instances."""
    mock_factory.clear_all() 