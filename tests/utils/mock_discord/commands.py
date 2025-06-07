"""
Discord Commands Mock
------------------
Mock classes for discord.ext.commands.
"""

from types import SimpleNamespace
from typing import Optional, Any, Callable, List, Dict
from dataclasses import dataclass, field

@dataclass
class Context:
    """Mock command context."""
    message: Any
    channel: Any
    author: Any
    guild: Any
    bot: Any = None
    prefix: str = "!"
    command: Any = None
    invoked_with: Optional[str] = None
    invoked_subcommand: Optional[Any] = None
    subcommand_passed: Optional[str] = None
    command_failed: bool = False
    
    async def send(self, content: Optional[str] = None, **kwargs) -> Any:
        """Mock send method."""
        return self.message

@dataclass
class Command:
    """Mock command."""
    name: str
    callback: Callable
    help: str = ""
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    hidden: bool = False
    enabled: bool = True
    cog: Any = None
    
    async def invoke(self, ctx: Context) -> Any:
        """Mock invoke method."""
        return await self.callback(ctx)

@dataclass
class Group(Command):
    """Mock command group."""
    commands: Dict[str, Command] = field(default_factory=dict)
    
    def command(self, *args, **kwargs):
        """Mock command decorator."""
        def decorator(func):
            cmd = Command(name=func.__name__, callback=func, *args, **kwargs)
            self.commands[cmd.name] = cmd
            return cmd
        return decorator

@dataclass
class Cog:
    """Mock cog."""
    name: str
    commands: List[Command] = field(default_factory=list)
    
    def cog_unload(self):
        """Mock cog unload."""
        pass

# Create a module-like object for commands
commands = SimpleNamespace(
    Context=Context,
    Command=Command,
    Group=Group,
    Cog=Cog,
    command=lambda *args, **kwargs: Command(name="test", callback=lambda: None, *args, **kwargs),
    group=lambda *args, **kwargs: Group(name="test", callback=lambda: None, *args, **kwargs)
)

__all__ = [
    'Context',
    'Command',
    'Group',
    'Cog',
    'commands'
] 