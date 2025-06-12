"""
Base command system for Dream.OS Discord bot.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum, auto

class CommandCategory(Enum):
    """Categories for organizing commands."""
    SYSTEM = auto()  # System management commands
    AGENT = auto()   # Agent control commands
    CHANNEL = auto() # Channel management commands
    UTILITY = auto() # Utility commands
    ADMIN = auto()   # Administrative commands

@dataclass
class CommandContext:
    """Context for command execution."""
    guild_id: int
    channel_id: int
    author_id: int
    author_name: str
    is_admin: bool = False
    raw_args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

class BaseCommand(ABC):
    """Base class for all commands."""
    
    def __init__(
        self,
        name: str,
        category: CommandCategory,
        description: str,
        usage: str,
        aliases: Optional[List[str]] = None,
        admin_only: bool = False,
        cooldown: Optional[int] = None
    ):
        """Initialize command.
        
        Args:
            name: Command name
            category: Command category
            description: Command description
            usage: Command usage string
            aliases: Optional command aliases
            admin_only: Whether command requires admin
            cooldown: Optional cooldown in seconds
        """
        self.name = name
        self.category = category
        self.description = description
        self.usage = usage
        self.aliases = aliases or []
        self.admin_only = admin_only
        self.cooldown = cooldown
        self._cooldown_users: Dict[int, float] = {}
    
    @abstractmethod
    async def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute the command.
        
        Args:
            ctx: Command context
            
        Returns:
            CommandResult
        """
        pass
    
    def check_cooldown(self, user_id: int) -> bool:
        """Check if user is on cooldown.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if user can use command
        """
        if not self.cooldown:
            return True
            
        import time
        current_time = time.time()
        last_used = self._cooldown_users.get(user_id, 0)
        
        if current_time - last_used < self.cooldown:
            return False
            
        self._cooldown_users[user_id] = current_time
        return True
    
    def get_help_text(self) -> str:
        """Get help text for command.
        
        Returns:
            str: Help text
        """
        help_text = f"**{self.name}** - {self.description}\n"
        help_text += f"Usage: {self.usage}\n"
        
        if self.aliases:
            help_text += f"Aliases: {', '.join(self.aliases)}\n"
            
        if self.admin_only:
            help_text += "**Admin only**\n"
            
        if self.cooldown:
            help_text += f"Cooldown: {self.cooldown}s\n"
            
        return help_text

class CommandRegistry:
    """Registry for managing commands."""
    
    def __init__(self):
        """Initialize registry."""
        self._commands: Dict[str, BaseCommand] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(self, command: BaseCommand) -> None:
        """Register a command.
        
        Args:
            command: Command to register
        """
        self._commands[command.name] = command
        
        for alias in command.aliases:
            self._aliases[alias] = command.name
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get command by name or alias.
        
        Args:
            name: Command name or alias
            
        Returns:
            Optional[BaseCommand]
        """
        # Check direct command name
        if name in self._commands:
            return self._commands[name]
            
        # Check aliases
        if name in self._aliases:
            return self._commands[self._aliases[name]]
            
        return None
    
    def get_commands_by_category(self) -> Dict[CommandCategory, List[BaseCommand]]:
        """Get commands grouped by category.
        
        Returns:
            Dict[CommandCategory, List[BaseCommand]]
        """
        categories: Dict[CommandCategory, List[BaseCommand]] = {}
        
        for command in self._commands.values():
            if command.category not in categories:
                categories[command.category] = []
            categories[command.category].append(command)
            
        return categories 