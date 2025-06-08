"""
Discord Client Mocks
------------------
Mock client classes for Discord.py testing.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from types import SimpleNamespace

from .models import MockGuild, MockMember, MockChannel, MockMessage

@dataclass
class MockCommand:
    """Mock Discord command."""
    name: str
    help: str = ""
    description: str = ""
    aliases: list = field(default_factory=list)
    hidden: bool = False
    enabled: bool = True
    cog: Any = None
    callback: Any = None

class ClientUser(MockMember):
    """Mock Discord client user."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = True
        self.system = False
        self.public_flags = 0
        self._state = SimpleNamespace()

    async def edit(self, **kwargs):
        """Edit the user."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

class Client:
    """Mock Discord client."""
    def __init__(self, *args, **kwargs):
        self.user = ClientUser(id=1, name="TestBot", bot=True)
        self.guilds = []
        self._closed = False
        self._ready = False
        self._ws = SimpleNamespace(closed=False)
        self._connection = SimpleNamespace(closed=False)
        self._handlers = {}
        self._listeners = {}
        self._cogs = {}
        self._commands = {}
        self._bot = None

    async def login(self, token: str, *args, **kwargs):
        """Mock login method."""
        self._ready = True
        return

    async def close(self):
        """Mock close method."""
        self._closed = True
        self._ws.closed = True
        self._connection.closed = True
        return

    async def start(self, token: str, *args, **kwargs):
        """Mock start method."""
        await self.login(token)
        return

    def is_ready(self) -> bool:
        """Check if client is ready."""
        return self._ready

    def is_closed(self) -> bool:
        """Check if client is closed."""
        return self._closed

    def get_cog(self, name: str) -> Optional[Any]:
        """Get a cog by name."""
        return self._cogs.get(name)

    def get_command(self, name: str) -> Optional[Any]:
        """Get a command by name."""
        return self._commands.get(name)

    def add_cog(self, cog: Any) -> None:
        """Add a cog."""
        self._cogs[cog.__cog_name__] = cog

    def remove_cog(self, name: str) -> Optional[Any]:
        """Remove a cog."""
        return self._cogs.pop(name, None)

    def add_command(self, command: Any) -> None:
        """Add a command."""
        self._commands[command.name] = command

    def remove_command(self, name: str) -> Optional[Any]:
        """Remove a command."""
        return self._commands.pop(name, None)

    def event(self, name=None):
        """Event decorator."""
        def wrapper(func):
            event_name = name or func.__name__
            self._handlers[event_name] = func
            return func
        return wrapper

    def listen(self, name=None):
        """Listener decorator."""
        def wrapper(func):
            event_name = name or func.__name__
            self._listeners[event_name] = func
            return func
        return wrapper

@dataclass
class MockBot:
    """Mock Discord bot."""
    name: str = "TestBot"
    commands: Dict[str, MockCommand] = field(default_factory=dict)
    cogs: Dict[str, Any] = field(default_factory=dict)
    guilds: List[MockGuild] = field(default_factory=list)
    user: ClientUser = field(default_factory=lambda: ClientUser(id=1, name="TestBot", bot=True))
    is_ready: bool = True
    is_closed: bool = False
    
    def get_command(self, name: str) -> Optional[MockCommand]:
        """Get a command by name."""
        return self.commands.get(name)
    
    def get_cog(self, name: str) -> Optional[Any]:
        """Get a cog by name."""
        return self.cogs.get(name)
    
    def get_guild(self, guild_id: int) -> Optional[MockGuild]:
        """Get a guild by ID."""
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild
        return None

@dataclass
class MockCog:
    """Mock Discord cog."""
    name: str = "TestCog"
    commands: List[MockCommand] = field(default_factory=list)

class VoiceClient:
    """Mock Discord VoiceClient class."""
    guild: Optional[MockGuild] = None
    channel: Optional[MockChannel] = None
    user: Optional[MockMember] = None
    is_connected: bool = False
    is_playing: bool = False
    
    async def connect(self, *args, **kwargs) -> None:
        """Mock connect method."""
        self.is_connected = True
    
    async def disconnect(self, *args, **kwargs) -> None:
        """Mock disconnect method."""
        self.is_connected = False
    
    async def play(self, *args, **kwargs) -> None:
        """Mock play method."""
        self.is_playing = True
    
    def stop(self, *args, **kwargs) -> None:
        """Mock stop method."""
        self.is_playing = False

class MockContext:
    """Minimal mock for Discord command context."""
    def __init__(self, author=None, channel=None, guild=None, message=None):
        self.author = author
        self.channel = channel
        self.guild = guild
        self.message = message
        self.command = None
        self.prefix = "!"
        self.invoked_with = None
        self.invoked_subcommand = None
        self.subcommand_passed = None
        self.command_failed = False

    async def send(self, content=None, **kwargs):
        """Send a message."""
        return content

    async def reply(self, content=None, **kwargs):
        """Reply to the message."""
        return content

__all__ = [
    'Client',
    'ClientUser',
    'MockBot',
    'MockCommand',
    'MockCog',
    'VoiceClient',
    'MockContext',
] 
