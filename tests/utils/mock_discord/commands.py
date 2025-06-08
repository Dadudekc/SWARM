"""
Discord Commands Mock
------------------
Mock classes for discord.ext.commands.
"""

from types import SimpleNamespace
from typing import Optional, Any, Callable, List, Dict, ForwardRef
from dataclasses import dataclass, field

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
    
    async def invoke(self, ctx: 'Context') -> Any:
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

@dataclass
class Bot:
    """Mock Discord bot."""
    name: str = "MockBot"
    commands: Dict[str, Command] = field(default_factory=dict)
    cogs: Dict[str, Cog] = field(default_factory=dict)
    is_ready: bool = False
    
    async def start(self, *args, **kwargs):
        """Mock start method."""
        self.is_ready = True
        
    async def close(self):
        """Mock close method."""
        self.is_ready = False
        
    def add_cog(self, cog: Cog):
        """Mock add_cog method."""
        self.cogs[cog.name] = cog
        
    def remove_cog(self, name: str):
        """Mock remove_cog method."""
        if name in self.cogs:
            del self.cogs[name]
            
    def get_cog(self, name: str) -> Optional[Cog]:
        """Mock get_cog method."""
        return self.cogs.get(name)
        
    def add_command(self, command: Command):
        """Mock add_command method."""
        self.commands[command.name] = command
        
    def remove_command(self, name: str):
        """Mock remove_command method."""
        if name in self.commands:
            del self.commands[name]
            
    def get_command(self, name: str) -> Optional[Command]:
        """Mock get_command method."""
        return self.commands.get(name)

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

# Create a module-like object for commands
commands = SimpleNamespace(
    Bot=Bot,
    Context=Context,
    Command=Command,
    Group=Group,
    Cog=Cog,
    command=lambda *args, **kwargs: Command(name="test", callback=lambda: None, *args, **kwargs),
    group=lambda *args, **kwargs: Group(name="test", callback=lambda: None, *args, **kwargs)
)

__all__ = [
    'Bot',
    'Context',
    'Command',
    'Group',
    'Cog',
    'commands'
] 