"""
Main Discord bot implementation.
"""

from tests.utils.mock_discord import (
    commands,
    Intents,
    Activity
)
from dreamos.core.discord_bot.activity import ActivityType
import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path
from dreamos.core.agent_control.system_orchestrator import SystemOrchestrator
from dreamos.core.log_manager import LogManager, LogLevel
from dreamos.utils.discord_client import Client, Command
from discord.ext import commands
from discord import Activity, ActivityType, Color, Embed
from .commands.base import CommandRegistry, CommandContext, CommandResult
from .commands.system import SystemStatusCommand, RestartCommand, MetricsCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DreamOSBot(commands.Bot):
    """Dream.OS Discord bot implementation."""
    
    def __init__(
        self,
        command_prefix: str = "!",
        metrics_enabled: bool = True,
        **kwargs
    ):
        """Initialize bot.
        
        Args:
            command_prefix: Command prefix
            metrics_enabled: Whether to enable metrics
            **kwargs: Additional bot options
        """
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            help_command=None  # Disable default help command
        )
        
        self.launch_time = datetime.now()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.orchestrator = None
        self.log_manager = None
        self.notifier = None
        
        # Set up metrics
        self.metrics_enabled = metrics_enabled
        if self.metrics_enabled:
            self.setup_metrics()
        
        self.command_registry = CommandRegistry()
        
        # Register system commands
        self.command_registry.register(SystemStatusCommand())
        self.command_registry.register(RestartCommand())
        self.command_registry.register(MetricsCommand())
        
        # Set up event handlers
        self.add_listener(self.on_ready, "on_ready")
        self.add_listener(self.on_message, "on_message")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load bot configuration.
        
        Returns:
            Dict containing bot configuration
        """
        config = {
            'log_dir': 'logs',
            'metrics_enabled': True,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'webhook_urls': {},
            'channel_assignments': {}
        }
        
        # Load from JSON
        config_path = Path("config/discord_bot.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        
        return config
    
    def setup_metrics(self):
        """Set up Prometheus metrics."""
        try:
            from prometheus_client import Counter, Gauge, Histogram
            
            # Command metrics
            self.command_counter = Counter(
                'discord_bot_commands_total',
                'Total number of commands executed',
                ['command', 'status']
            )
            
            self.command_latency = Histogram(
                'discord_bot_command_latency_seconds',
                'Command execution latency',
                ['command']
            )
            
            # Message metrics
            self.message_counter = Counter(
                'discord_bot_messages_total',
                'Total number of messages processed',
                ['type', 'status']
            )
            
            # System metrics
            self.system_status = Gauge(
                'discord_bot_system_status',
                'System component status',
                ['component']
            )
            
        except ImportError:
            self.logger.warning("Prometheus client not installed, metrics disabled")
            self.metrics_enabled = False
    
    async def setup_hook(self):
        """Set up bot hooks and initialize components."""
        try:
            # Initialize orchestrator
            from dreamos.core.agent_control.system_orchestrator import SystemOrchestrator
            self.orchestrator = SystemOrchestrator()
            await self.orchestrator.initialize()
            
            # Initialize log manager
            from dreamos.core.log_manager import LogManager
            self.log_manager = LogManager(
                log_dir=Path(self.config['log_dir']),
                max_size=1024 * 1024,  # 1MB
                backup_count=5
            )
            
            # Initialize notifier
            from .notifier import DiscordNotifier
            self.notifier = DiscordNotifier(self)
            
            # Load cogs
            await self.load_cogs()
            
            self.logger.info("Bot setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during bot setup: {e}")
            raise
    
    async def load_cogs(self):
        """Load bot cogs."""
        try:
            # Load core cogs
            await self.load_extension("discord_bot.cogs.help_menu")
            await self.load_extension("discord_bot.cogs.agent_commands")
            await self.load_extension("discord_bot.cogs.system_commands")
            await self.load_extension("discord_bot.cogs.channel_commands")
            
            self.logger.info("Cogs loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading cogs: {e}")
            raise
    
    async def on_ready(self):
        """Handle bot ready event."""
        self.logger.info(f"Bot is ready! Logged in as {self.user}")
        
        # Set bot activity
        await self.change_presence(
            activity=Activity(
                type=ActivityType.watching,
                name="Dream.OS Swarm"
            )
        )
        
        # Initialize system status
        if self.metrics_enabled:
            self.system_status.labels('bot').set(1)
    
    async def on_message(self, message):
        """Handle incoming messages.
        
        Args:
            message: Discord message
        """
        # Ignore messages from self
        if message.author == self.user:
            return
            
        # Check if message is a command
        if not message.content.startswith(self.command_prefix):
            return
            
        # Parse command
        content = message.content[len(self.command_prefix):].strip()
        command_name = content.split()[0]
        args = content.split()[1:]
        
        # Get command
        command = self.command_registry.get_command(command_name)
        if not command:
            await message.channel.send(f"Unknown command: {command_name}")
            return
            
        # Check cooldown
        if not command.check_cooldown(message.author.id):
            await message.channel.send("Command is on cooldown")
            return
            
        # Check admin permission
        if command.admin_only and not message.author.guild_permissions.administrator:
            await message.channel.send("This command requires administrator permissions")
            return
            
        # Create command context
        ctx = CommandContext(
            guild_id=message.guild.id if message.guild else 0,
            channel_id=message.channel.id,
            author_id=message.author.id,
            author_name=str(message.author),
            is_admin=message.author.guild_permissions.administrator if message.guild else False,
            raw_args=args
        )
        
        try:
            # Execute command
            result = await command.execute(ctx)
            
            # Send response
            if result.success:
                await message.channel.send(result.message)
            else:
                await message.channel.send(f"Error: {result.message}")
                
            # Log error if any
            if result.error:
                self.logger.error(
                    f"Command error: {result.error}",
                    exc_info=True,
                    extra={
                        "command": command_name,
                        "user": message.author.id,
                        "guild": message.guild.id if message.guild else 0
                    }
                )
                
        except Exception as e:
            self.logger.error(
                f"Unexpected error in command {command_name}: {e}",
                exc_info=True,
                extra={
                    "command": command_name,
                    "user": message.author.id,
                    "guild": message.guild.id if message.guild else 0
                }
            )
            await message.channel.send("An unexpected error occurred")
    
    def get_help_embed(self) -> Embed:
        """Get help embed.
        
        Returns:
            Embed: Help embed
        """
        embed = Embed(
            title="Dream.OS Bot Help",
            description="Available commands:",
            color=Color.blue()
        )
        
        # Group commands by category
        for category, commands in self.command_registry.get_commands_by_category().items():
            if not commands:
                continue
                
            commands_list = []
            for cmd in commands:
                commands_list.append(cmd.get_help_text())
                
            embed.add_field(
                name=category.name.title(),
                value="\n".join(commands_list),
                inline=False
            )
            
        return embed

async def main():
    """Main entry point for the bot."""
    bot = DreamOSBot()
    
    try:
        async with bot:
            await bot.start(bot.config.get("token"))
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
