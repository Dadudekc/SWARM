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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DreamOSBot(commands.Bot):
    """Dream.OS Discord bot implementation."""
    
    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the bot.
        
        Sets up intents, loads configuration, and initializes core components.
        """
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
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
        self.metrics_enabled = self.config.get('metrics_enabled', True)
        if self.metrics_enabled:
            self.setup_metrics()
    
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
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors.
        
        Args:
            ctx: Command context
            error: Exception that occurred
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use !help to see available commands.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        else:
            self.logger.error(f"Command error: {error}")
            await ctx.send("An error occurred while processing the command.")
            
            if self.metrics_enabled:
                self.command_counter.labels(
                    command=ctx.command.name if ctx.command else 'unknown',
                    status='error'
                ).inc()

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
