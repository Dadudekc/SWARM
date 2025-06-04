"""
Dream.OS Discord Bot

Provides Discord interface for Dream.OS system.
"""

import os
import logging
import discord
from discord.ext import commands
from .cogs import BasicCommands
from pathlib import Path
from dreamos.core.agent_control.system_orchestrator import SystemOrchestrator
from social.utils.log_manager import LogManager, LogLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

class DreamOSBot(commands.Bot):
    """Dream.OS Discord bot."""
    
    def __init__(self):
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize system orchestrator
        self.runtime_dir = Path("runtime")
        self.runtime_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        self.log_manager = LogManager({
            'log_dir': str(self.runtime_dir / "logs"),
            'level': LogLevel.INFO,
            'platforms': {
                'discord': 'discord.log',
                'commands': 'commands.log'
            }
        })
        
        self.orchestrator = SystemOrchestrator(
            runtime_dir=self.runtime_dir,
            discord_token=os.getenv("DISCORD_TOKEN"),
            channel_id=int(os.getenv("DISCORD_CHANNEL_ID"))
        )
        
        self.log_manager.info(
            platform="discord",
            status="success",
            message="Discord bot initialized",
            tags=["startup", "init"]
        )
        
    async def setup_hook(self):
        """Set up bot commands and start system."""
        try:
            # Start system orchestrator
            await self.orchestrator.start()
            
            # Add command cog
            await self.add_cog(BasicCommands(self.orchestrator, self.log_manager))
            
            self.log_manager.info(
                platform="discord",
                status="success",
                message="Bot commands set up successfully",
                tags=["startup", "commands"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="discord",
                status="error",
                message=f"Failed to set up bot: {str(e)}",
                tags=["startup", "error"]
            )
            raise
        
    async def on_ready(self):
        """Handle bot ready event."""
        self.log_manager.info(
            platform="discord",
            status="success",
            message=f"Bot connected as {self.user}",
            tags=["startup", "ready"]
        )
        
            
    async def close(self):
        """Clean up resources when bot is shutting down."""
        try:
            # Stop system orchestrator
            await self.orchestrator.stop()
            
            self.log_manager.info(
                platform="discord",
                status="success",
                message="Bot shutting down",
                tags=["shutdown"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="discord",
                status="error",
                message=f"Error during shutdown: {str(e)}",
                tags=["shutdown", "error"]
            )
            
        finally:
            await super().close()

def main():
    """Run the bot."""
    bot = DreamOSBot()
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    main() 