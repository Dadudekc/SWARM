"""
Mock Discord classes for testing.
"""

from typing import Optional, List, Dict, Any, Union, Callable, Coroutine, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from functools import wraps
from types import SimpleNamespace

T = TypeVar('T')

# Mock Discord.py classes
class Cog:
    """Mock Discord Cog class."""
    def __init__(self, bot=None):
        self.bot = bot

    def cog_unload(self):
        """Unload the cog."""
        pass

class Guild:
    """Mock Discord Guild class."""
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class Context:
    """Mock Discord Context class."""
    def __init__(self, message=None, channel=None, author=None, guild=None):
        self.message = message
        self.channel = channel
        self.author = author
        self.guild = guild

class CommandError(Exception):
    """Mock Discord CommandError class."""
    pass

class Client:
    """Mock Discord client."""
    def __init__(self, *args, **kwargs):
        self.user = None
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

@dataclass
class Command:
    """Mock Discord command."""
    name: str
    help: str = ""
    description: str = ""
    aliases: list = field(default_factory=list)
    hidden: bool = False
    enabled: bool = True
    cog: Any = None
    callback: Any = None

# Create commands namespace after all relevant classes are defined
commands = SimpleNamespace()
commands.Cog = Cog
commands.Command = Command
commands.CommandError = CommandError
commands.Context = Context
commands.Client = Client
commands.Bot = Client  # Use Client as the base for Bot

# Mock Color class for embed color handling (test stub)
class Color:
    def __init__(self, value=0):
        self.value = value
    @classmethod
    def default(cls):
        return cls(0)
    @classmethod
    def blue(cls):
        return cls(0x3498db)
    @classmethod
    def red(cls):
        return cls(0xe74c3c)
    @classmethod
    def green(cls):
        return cls(0x2ecc71)
    def __int__(self):
        return self.value

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

@dataclass
class MockGuild:
    """Mock Discord guild."""
    id: int
    name: str
    channels: List['MockChannel'] = field(default_factory=list)
    members: List['MockMember'] = field(default_factory=list)
    roles: List['MockRole'] = field(default_factory=list)
    
    def get_channel(self, channel_id: int) -> Optional['MockChannel']:
        """Get a channel by ID."""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None
    
    def get_member(self, member_id: int) -> Optional['MockMember']:
        """Get a member by ID."""
        for member in self.members:
            if member.id == member_id:
                return member
        return None

@dataclass
class MockMember:
    """Mock Discord member."""
    id: int
    name: str
    display_name: Optional[str] = None
    bot: bool = False
    
    @property
    def mention(self) -> str:
        """Get the member's mention string."""
        return f"<@{self.id}>"

@dataclass
class MockRole:
    """Mock Discord role."""
    id: int
    name: str
    guild: Optional[MockGuild] = None
    color: int = 0
    position: int = 0

@dataclass
class MockChannel:
    """Mock Discord channel."""
    id: int
    name: str
    guild: Optional[MockGuild] = None
    type: str = "text"
    position: int = 0
    
    async def send(self, content: Optional[str] = None, **kwargs) -> 'MockMessage':
        """Send a message to the channel."""
        return MockMessage(
            id=1,
            content=content or "",
            channel=self,
            author=MockMember(id=1, name="Bot")
        )

@dataclass
class MockMessage:
    """Mock Discord message."""
    id: int
    content: str
    channel: MockChannel
    author: MockMember
    created_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    embeds: List[Dict[str, Any]] = field(default_factory=list)
    
    async def edit(self, **kwargs) -> None:
        """Edit the message."""
        if "content" in kwargs:
            self.content = kwargs["content"]
        self.edited_at = datetime.now()

@dataclass
class MockEmbed:
    """Mock Discord embed."""
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[int] = None
    url: Optional[str] = None
    fields: List[Dict[str, Any]] = field(default_factory=list)
    footer: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    thumbnail: Optional[Dict[str, str]] = None
    author: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None
    
    def add_field(self, name: str, value: str, inline: bool = False) -> None:
        """Add a field to the embed."""
        self.fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })
    
    def set_footer(self, text: str, icon_url: Optional[str] = None) -> None:
        """Set the embed footer."""
        self.footer = {"text": text, "icon_url": icon_url}
    
    def set_image(self, url: str) -> None:
        """Set the embed image."""
        self.image = {"url": url}
    
    def set_thumbnail(self, url: str) -> None:
        """Set the embed thumbnail."""
        self.thumbnail = {"url": url}
    
    def set_author(self, name: str, icon_url: Optional[str] = None) -> None:
        """Set the embed author."""
        self.author = {"name": name, "icon_url": icon_url}

@dataclass
class MockBot:
    """Mock Discord bot."""
    name: str = "TestBot"
    commands: Dict[str, MockCommand] = field(default_factory=dict)
    cogs: Dict[str, Any] = field(default_factory=dict)
    guilds: List[MockGuild] = field(default_factory=list)
    user: MockMember = field(default_factory=lambda: MockMember(id=1, name="TestBot", bot=True))
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
class MockContext:
    """Mock Discord command context."""
    message: MockMessage = None
    channel: MockChannel = None
    author: MockMember = None
    guild: Optional[MockGuild] = None
    bot: Optional[MockBot] = None
    prefix: str = "!"
    command: Optional[MockCommand] = None
    invoked_with: Optional[str] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    # Allow no-argument instantiation for test compatibility
    def __init__(self, message=None, channel=None, author=None, guild=None, bot=None, prefix="!", command=None, invoked_with=None, args=None, kwargs=None):
        self.message = message if message is not None else MockMessage(id=1, content="", channel=MockChannel(id=1, name="test"), author=MockMember(id=1, name="TestUser"))
        self.channel = channel if channel is not None else self.message.channel
        self.author = author if author is not None else self.message.author
        self.guild = guild
        self.bot = bot
        self.prefix = prefix
        self.command = command
        self.invoked_with = invoked_with
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
    
    async def send(self, content: Optional[str] = None, **kwargs) -> MockMessage:
        """Send a message in the context."""
        return await self.channel.send(content, **kwargs)
    
    async def reply(self, content: Optional[str] = None, **kwargs) -> MockMessage:
        """Reply to the message in the context."""
        return await self.send(content, **kwargs)
    
    async def trigger_typing(self) -> None:
        """Trigger typing indicator."""
        pass

@dataclass
class MockCog:
    """Mock Discord cog."""
    name: str = "TestCog"
    commands: List[MockCommand] = field(default_factory=list)

def create_mock_guild(guild_id: int = 1, name: str = "Test Guild") -> MockGuild:
    """Create a mock guild with some test data."""
    guild = MockGuild(id=guild_id, name=name)
    
    # Add some test members
    members = [
        MockMember(id=1, name="Test User", guild=guild),
        MockMember(id=2, name="Test Bot", guild=guild, bot=True)
    ]
    guild.members = members
    
    # Add some test roles
    roles = [
        MockRole(id=1, name="Admin", guild=guild, position=1),
        MockRole(id=2, name="User", guild=guild, position=0)
    ]
    guild.roles = roles
    
    # Add some test channels
    channels = [
        MockChannel(id=1, name="general", guild=guild),
        MockChannel(id=2, name="test", guild=guild)
    ]
    guild.channels = channels
    
    return guild

def create_mock_context(
    guild: Optional[MockGuild] = None,
    channel_id: int = 1,
    author_id: int = 1
) -> MockContext:
    """Create a mock context with some test data."""
    if guild is None:
        guild = create_mock_guild()
    
    channel = next(c for c in guild.channels if c.id == channel_id)
    author = next(m for m in guild.members if m.id == author_id)
    
    message = MockMessage(
        id=1,
        content="!test",
        author=author,
        channel=channel,
        guild=guild
    )
    
    return MockContext(
        message=message,
        author=author,
        channel=channel,
        guild=guild
    )

def create_mock_bot() -> MockBot:
    """Create a mock bot with some test data."""
    bot = MockBot()
    bot.guilds = [create_mock_guild()]
    return bot

def create_mock_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[int] = None,
    url: Optional[str] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[Dict[str, str]] = None,
    image: Optional[Dict[str, str]] = None,
    thumbnail: Optional[Dict[str, str]] = None,
    author: Optional[Dict[str, str]] = None,
    timestamp: Optional[datetime] = None
) -> MockEmbed:
    """Create a mock Discord embed."""
    embed = MockEmbed(
        title=title,
        description=description,
        color=color,
        url=url,
        fields=fields or [],
        footer=footer,
        image=image,
        thumbnail=thumbnail,
        author=author,
        timestamp=timestamp
    )
    return embed

def run_async_test(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async test and return its result."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def async_test(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """Decorator to run an async test."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return run_async_test(func(*args, **kwargs))
    return wrapper

# Add a mock command decorator to the commands namespace
# This mimics discord.ext.commands.command

def mock_command_decorator(*args, **kwargs):
    def decorator(func):
        func.name = kwargs.get('name', func.__name__)
        return func
    return decorator
commands.command = mock_command_decorator

# Place these at the end to avoid NameError and avoid shadowing the real discord package
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

@dataclass
class Interaction:
    """Mock Discord Interaction class."""
    id: int = 1
    type: int = 2  # ApplicationCommand
    data: Dict[str, Any] = field(default_factory=dict)
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    member: Optional[MockMember] = None
    user: Optional[MockMember] = None
    token: str = "mock_token"
    version: int = 1
    application_id: int = 1
    message: Optional[MockMessage] = None
    
    async def response(self, **kwargs) -> None:
        """Send a response to the interaction."""
        pass
    
    async def followup(self, **kwargs) -> MockMessage:
        """Send a followup message."""
        return MockMessage(
            id=1,
            content=kwargs.get("content", ""),
            channel=MockChannel(id=1, name="test"),
            author=MockMember(id=1, name="Bot")
        )

class View:
    """Mock Discord View class."""
    children: List[Any] = field(default_factory=list)
    
    def add_item(self, item: Any) -> None:
        """Add an item to the view."""
        self.children.append(item)

ui = SimpleNamespace()
ui.View = View
mock_discord_ns = SimpleNamespace()
mock_discord_ns.ui = ui
mock_discord_ns.Embed = MockEmbed

# For legacy compatibility with test setup (conftest.py), allow monkeypatching as 'discord'.
discord = mock_discord_ns 