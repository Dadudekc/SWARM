"""
Main Discord bot implementation.
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path
from dreamos.core.agent_control.system_orchestrator import SystemOrchestrator
from social.utils.log_manager import LogManager, LogLevel
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
        """Initialize the bot."""
        intents = discord.Intents.default()
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
    
    def _load_config(self) -> Dict[str, Any]:
        """Load bot configuration from file.
        
        Returns:
            Dict containing bot configuration
        """
        config_path = Path("config/discord_bot.json")
        if not config_path.exists():
            self.logger.warning("No config file found, using defaults")
            return {
                "token": os.getenv("DISCORD_TOKEN"),
                "owner_id": int(os.getenv("OWNER_ID", "0")),
                "log_level": "INFO"
            }
        
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    async def setup_hook(self):
        """Set up the bot's components and cogs."""
        try:
            # Load cogs
            for cog_file in Path("discord_bot/cogs").glob("*.py"):
                if cog_file.stem != "__init__":
                    try:
                        await self.load_extension(f"discord_bot.cogs.{cog_file.stem}")
                        self.logger.info(f"Loaded cog: {cog_file.stem}")
                    except Exception as e:
                        self.logger.error(f"Failed to load cog {cog_file.stem}: {e}")
            
            # Initialize components
            # TODO: Initialize orchestrator and log manager
            
        except Exception as e:
            self.logger.error(f"Error in setup_hook: {e}")
    
    async def on_ready(self):
        """Handle bot ready event."""
        self.logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Dream.OS"
            )
        )
    
    async def on_command_error(self, ctx: Any, error: Any):
        """Handle command errors.
        
        Args:
            ctx: Command context
            error: Command error
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