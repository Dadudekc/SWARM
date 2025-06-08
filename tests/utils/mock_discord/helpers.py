"""
Discord Helper Functions
----------------------
Helper functions for Discord.py testing.
"""

from typing import Optional, List, Dict, Any, Callable, Coroutine, TypeVar, BinaryIO, Union
from functools import wraps
from datetime import datetime
import tempfile

from .models import MockGuild, MockChannel, MockMember, MockMessage, MockEmbed
from .client import MockBot, MockCommand, MockContext
from .webhook import MockWebhook, MockFile

T = TypeVar('T')

def create_mock_guild(guild_id: int = 1, name: str = "Test Guild") -> MockGuild:
    """Create a mock guild.
    
    Args:
        guild_id: Guild ID
        name: Guild name
        
    Returns:
        Mock guild instance
    """
    return MockGuild(
        id=guild_id,
        name=name,
        channels=[],
        members=[],
        roles=[]
    )

def create_mock_context(
    guild: Optional[MockGuild] = None,
    channel_id: int = 1,
    author_id: int = 1
) -> MockContext:
    """Create a mock context.
    
    Args:
        guild: Optional guild
        channel_id: Channel ID
        author_id: Author ID
        
    Returns:
        Mock context instance
    """
    if guild is None:
        guild = create_mock_guild()
    
    channel = MockChannel(id=channel_id, name="test", guild=guild)
    author = MockMember(id=author_id, name="TestUser")
    
    return MockContext(
        message=MockMessage(
            id=1,
            content="test",
            channel=channel,
            author=author
        ),
        channel=channel,
        author=author,
        guild=guild
    )

def create_mock_bot() -> MockBot:
    """Create a mock bot.
    
    Returns:
        Mock bot instance
    """
    return MockBot()

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
    """Create a mock embed.
    
    Args:
        title: Optional title
        description: Optional description
        color: Optional color
        url: Optional URL
        fields: Optional fields
        footer: Optional footer
        image: Optional image
        thumbnail: Optional thumbnail
        author: Optional author
        timestamp: Optional timestamp
        
    Returns:
        Mock embed instance
    """
    embed = MockEmbed(
        title=title,
        description=description,
        color=color,
        url=url,
        timestamp=timestamp
    )
    
    if fields:
        for field in fields:
            embed.add_field(**field)
    
    if footer:
        embed.set_footer(**footer)
    
    if image:
        embed.set_image(**image)
    
    if thumbnail:
        embed.set_thumbnail(**thumbnail)
    
    if author:
        embed.set_author(**author)
    
    return embed

def create_mock_webhook(
    webhook_id: int = 1,
    token: str = "test_token",
    url: str = "https://discord.com/api/webhooks/test",
    channel_id: int = 1,
    guild_id: Optional[int] = None,
    name: Optional[str] = None
) -> MockWebhook:
    """Create a mock webhook.
    
    Args:
        webhook_id: Webhook ID
        token: Webhook token
        url: Webhook URL
        channel_id: Channel ID
        guild_id: Optional guild ID
        name: Optional webhook name
        
    Returns:
        Mock webhook instance
    """
    return MockWebhook(
        id=webhook_id,
        token=token,
        url=url,
        channel_id=channel_id,
        guild_id=guild_id,
        name=name
    )

def create_mock_file(
    filename: str = "test.txt",
    content: Union[str, bytes] = "Test content",
    description: Optional[str] = None,
    spoiler: bool = False
) -> MockFile:
    """Create a mock file.
    
    Args:
        filename: File name
        content: File content (string or bytes)
        description: Optional file description
        spoiler: Whether file is a spoiler
        
    Returns:
        Mock file instance
    """
    return MockFile(
        filename=filename,
        content=content,
        description=description,
        spoiler=spoiler
    )

def run_async_test(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async test.
    
    Args:
        coro: Coroutine to run
        
    Returns:
        Coroutine result
    """
    import asyncio
    return asyncio.run(coro)

def async_test(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """Decorator for async tests.
    
    Args:
        func: Async test function
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return run_async_test(func(*args, **kwargs))
    return wrapper

def mock_command_decorator(*args, **kwargs):
    """Decorator for mock commands.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Decorated function
    """
    def decorator(func):
        return MockCommand(
            name=func.__name__,
            callback=func,
            **kwargs
        )
    return decorator

__all__ = [
    'create_mock_guild',
    'create_mock_context',
    'create_mock_bot',
    'create_mock_embed',
    'create_mock_webhook',
    'create_mock_file',
    'run_async_test',
    'async_test',
    'mock_command_decorator'
] 
