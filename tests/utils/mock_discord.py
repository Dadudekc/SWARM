"""Mock Discord objects for testing."""

from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field

# Mock Discord.py classes
class Guild:
    """Mock Discord Guild."""
    def __init__(self, id: int = 123456789, name: str = "Test Guild"):
        self.id = id
        self.name = name
        self.members: List[Member] = []
        self.channels: List[TextChannel] = []

class Member:
    """Mock Discord Member."""
    def __init__(self, id: int = 123456789, name: str = "Test User", bot: bool = False):
        self.id = id
        self.name = name
        self.bot = bot
        self.guild: Optional[Guild] = None

class TextChannel:
    """Mock Discord Text Channel."""
    def __init__(self, id: int = 123456789, name: str = "test-channel"):
        self.id = id
        self.name = name
        self.guild: Optional[Guild] = None
        self.messages: List[Message] = []

    async def send(self, content: Optional[str] = None, **kwargs) -> 'Message':
        """Mock sending a message."""
        message = Message(
            id=len(self.messages) + 1,
            content=content,
            channel=self,
            **kwargs
        )
        self.messages.append(message)
        return message

class Message:
    """Mock Discord Message."""
    def __init__(
        self,
        id: int = 123456789,
        content: Optional[str] = None,
        channel: Optional[TextChannel] = None,
        author: Optional[Member] = None,
        **kwargs
    ):
        self.id = id
        self.content = content
        self.channel = channel
        self.author = author or Member()
        self.created_at = datetime.now()
        self.embeds: List[Embed] = []
        if 'embed' in kwargs:
            self.embeds.append(kwargs['embed'])

class Context:
    """Mock Discord Context."""
    def __init__(
        self,
        message: Optional[Message] = None,
        channel: Optional[TextChannel] = None,
        author: Optional[Member] = None,
        guild: Optional[Guild] = None
    ):
        self.message = message or Message()
        self.channel = channel or TextChannel()
        self.author = author or Member()
        self.guild = guild or Guild()
        self.bot = None  # Will be set by the bot

    async def send(self, content: Optional[str] = None, **kwargs) -> Message:
        """Mock sending a message in context."""
        return await self.channel.send(content, **kwargs)

@dataclass
class Embed:
    """Mock Discord Embed."""
    title: Optional[str] = None
    description: Optional[str] = None
    color: int = 0x000000
    fields: List[Dict[str, Any]] = field(default_factory=list)
    footer: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    thumbnail: Optional[Dict[str, str]] = None
    author: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None

    def add_field(self, name: str, value: str, inline: bool = True) -> None:
        """Add a field to the embed."""
        self.fields.append({
            "name": name,
            "value": value,
            "inline": inline
        })

# Mock discord.ext.commands
class CommandError(Exception):
    """Base class for command errors."""
    pass

class CommandNotFound(CommandError):
    """Command not found error."""
    pass

class MissingRequiredArgument(CommandError):
    """Missing required argument error."""
    pass

class BadArgument(CommandError):
    """Bad argument error."""
    pass

class Command:
    """Mock Discord command."""
    def __init__(
        self,
        name: str,
        callback: Callable,
        help: Optional[str] = None,
        brief: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.callback = callback
        self.help = help
        self.brief = brief
        self.description = description
        self.kwargs = kwargs

class Bot:
    """Mock Discord bot."""
    def __init__(self, command_prefix: str = "!"):
        self.command_prefix = command_prefix
        self.commands: Dict[str, Command] = {}
        self.guilds: List[Guild] = []

    def command(self, name: Optional[str] = None, **kwargs):
        """Decorator to register a command."""
        def decorator(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = Command(cmd_name, func, **kwargs)
            return func
        return decorator

    async def get_context(self, message: Message) -> Context:
        """Get context for a message."""
        return Context(message=message)

    async def process_commands(self, message: Message) -> None:
        """Process commands in a message."""
        if not message.content.startswith(self.command_prefix):
            return

        content = message.content[len(self.command_prefix):].strip()
        command_name = content.split()[0]
        
        if command_name in self.commands:
            ctx = await self.get_context(message)
            try:
                await self.commands[command_name].callback(ctx)
            except Exception as e:
                await self.on_command_error(ctx, e)

    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        """Handle command errors."""
        if isinstance(error, CommandNotFound):
            await ctx.send(f"Command not found: {error}")
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error}")
        elif isinstance(error, BadArgument):
            await ctx.send(f"Bad argument: {error}")
        else:
            await ctx.send(f"An error occurred: {error}")

# Create a mock commands module
class commands:
    """Mock discord.ext.commands module."""
    Command = Command
    Bot = Bot
    CommandError = CommandError
    CommandNotFound = CommandNotFound
    MissingRequiredArgument = MissingRequiredArgument
    BadArgument = BadArgument

# Create a mock discord.ext module
class ext:
    """Mock discord.ext module."""
    commands = commands

# Create a mock discord module
discord = type('discord', (), {
    'Guild': Guild,
    'Member': Member,
    'TextChannel': TextChannel,
    'Message': Message,
    'Context': Context,
    'Embed': Embed,
    'ext': ext
})()

def create_mock_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: int = 0x000000,
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[Dict[str, str]] = None,
    image: Optional[Dict[str, str]] = None,
    thumbnail: Optional[Dict[str, str]] = None,
    author: Optional[Dict[str, str]] = None,
    timestamp: Optional[datetime] = None
) -> Embed:
    """Create a mock Discord embed."""
    return Embed(
        title=title,
        description=description,
        color=color,
        fields=fields or [],
        footer=footer,
        image=image,
        thumbnail=thumbnail,
        author=author,
        timestamp=timestamp
    )

def create_mock_context(
    message: Optional[Message] = None,
    channel: Optional[TextChannel] = None,
    author: Optional[Member] = None,
    guild: Optional[Guild] = None
) -> Context:
    """Create a mock Discord context."""
    return Context(message, channel, author, guild)

def create_mock_guild(
    id: int = 123456789,
    name: str = "Test Guild"
) -> Guild:
    """Create a mock Discord guild."""
    return Guild(id, name)

def create_mock_member(
    id: int = 123456789,
    name: str = "Test User",
    bot: bool = False
) -> Member:
    """Create a mock Discord member."""
    return Member(id, name, bot)

def create_mock_channel(
    id: int = 123456789,
    name: str = "test-channel"
) -> TextChannel:
    """Create a mock Discord text channel."""
    return TextChannel(id, name)

def create_mock_message(
    id: int = 123456789,
    content: Optional[str] = None,
    channel: Optional[TextChannel] = None,
    author: Optional[Member] = None
) -> Message:
    """Create a mock Discord message."""
    return Message(id, content, channel, author)

class MockMessage:
    """Mock Discord message object."""
    
    def __init__(self, content: str = '', **kwargs):
        self.content = content
        self.author = kwargs.get('author', MockUser())
        self.channel = kwargs.get('channel', MockChannel())
        self.guild = kwargs.get('guild', MockGuild())
        self.embeds: List[MockEmbed] = []
        
    async def add_reaction(self, emoji: str) -> None:
        """Add a reaction to the message."""
        pass
        
    async def remove_reaction(self, emoji: str, user: Any) -> None:
        """Remove a reaction from the message."""
        pass

class MockUser:
    """Mock Discord user object."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.name = kwargs.get('name', 'Mock User')
        self.discriminator = kwargs.get('discriminator', '0000')
        self.bot = kwargs.get('bot', False)
        self.avatar_url = kwargs.get('avatar_url', None)

class MockChannel:
    """Mock Discord channel object."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.name = kwargs.get('name', 'mock-channel')
        self.guild = kwargs.get('guild', MockGuild())
        
    async def send(self, content: str = None, **kwargs) -> MockMessage:
        """Send a message to the channel."""
        return MockMessage(content=content, **kwargs)

class MockGuild:
    """Mock Discord guild object."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.name = kwargs.get('name', 'Mock Guild')
        self.members: List[MockUser] = kwargs.get('members', [])
        self.channels: List[MockChannel] = kwargs.get('channels', [])
        
    def get_member(self, user_id: int) -> Optional[MockUser]:
        """Get a member by ID."""
        return next((m for m in self.members if m.id == user_id), None)
        
    def get_channel(self, channel_id: int) -> Optional[MockChannel]:
        """Get a channel by ID."""
        return next((c for c in self.channels if c.id == channel_id), None)

async def send_message(
    channel: MockChannel,
    content: Optional[str] = None,
    embed: Optional[MockEmbed] = None,
    **kwargs
) -> MockMessage:
    """Send a message to a Discord channel.
    
    Args:
        channel: The channel to send the message to
        content: The message content
        embed: Optional embed to include
        **kwargs: Additional message parameters
        
    Returns:
        The sent message
    """
    message = await channel.send(content=content, **kwargs)
    if embed:
        message.embeds.append(embed)
    return message 