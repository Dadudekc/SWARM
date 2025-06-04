"""
Dream.OS Discord Bot

Provides Discord interface for Dream.OS system.
"""

import os
import logging
import discord
from discord.ext import commands
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
            
            # Add commands
            self.add_command(commands.Command(self.cmd_help, name="help"))
            self.add_command(commands.Command(self.cmd_status, name="status"))
            self.add_command(commands.Command(self.cmd_task, name="task"))
            self.add_command(commands.Command(self.cmd_devlog, name="devlog"))
            
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
        
    async def cmd_help(self, ctx):
        """Show help information."""
        try:
            help_text = """
**Dream.OS Bot Commands**

`!help` - Show this help message
`!status <agent_id>` - Show agent status
`!task <agent_id> <title> <description>` - Create new task
`!devlog <agent_id> <category> <content>` - Add devlog entry
            """
            await ctx.send(help_text)
            
            self.log_manager.info(
                platform="commands",
                status="success",
                message=f"Help command executed by {ctx.author}",
                tags=["command", "help"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="commands",
                status="error",
                message=f"Error in help command: {str(e)}",
                tags=["command", "help", "error"]
            )
            await ctx.send("Error showing help information")
        
    async def cmd_status(self, ctx, agent_id: str):
        """Show agent status."""
        try:
            status = await self.orchestrator.get_agent_status(agent_id)
            
            # Format status message
            msg = f"**Status for Agent {agent_id}**\n\n"
            
            # Tasks section
            msg += "**Tasks**\n"
            msg += f"Total: {status['tasks']['total']}\n"
            msg += f"Summary: {status['tasks']['summary']}\n\n"
            
            # Devlog section
            msg += "**DevLog**\n"
            msg += f"Total Entries: {status['devlog']['total_entries']}\n\n"
            
            # Messages section
            msg += "**Messages**\n"
            msg += f"Total: {status['messages']['total']}\n"
            
            await ctx.send(msg)
            
            self.log_manager.info(
                platform="commands",
                status="success",
                message=f"Status command executed for agent {agent_id} by {ctx.author}",
                tags=["command", "status"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="commands",
                status="error",
                message=f"Error in status command for agent {agent_id}: {str(e)}",
                tags=["command", "status", "error"]
            )
            await ctx.send(f"Error getting status: {str(e)}")
            
    async def cmd_task(self, ctx, agent_id: str, title: str, *, description: str):
        """Create new task."""
        try:
            task_id = await self.orchestrator.create_agent_task(
                agent_id=agent_id,
                title=title,
                description=description
            )
            
            await ctx.send(f"Task created with ID: {task_id}")
            
            self.log_manager.info(
                platform="commands",
                status="success",
                message=f"Task command executed for agent {agent_id} by {ctx.author}",
                tags=["command", "task"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="commands",
                status="error",
                message=f"Error in task command for agent {agent_id}: {str(e)}",
                tags=["command", "task", "error"]
            )
            await ctx.send(f"Error creating task: {str(e)}")
            
    async def cmd_devlog(self, ctx, agent_id: str, category: str, *, content: str):
        """Add devlog entry."""
        try:
            await self.orchestrator.devlog_manager.add_devlog_entry(
                agent_id=agent_id,
                category=category,
                content=content,
                author=str(ctx.author)
            )
            
            await ctx.send("Devlog entry added successfully")
            
            self.log_manager.info(
                platform="commands",
                status="success",
                message=f"Devlog command executed for agent {agent_id} by {ctx.author}",
                tags=["command", "devlog"]
            )
            
        except Exception as e:
            self.log_manager.error(
                platform="commands",
                status="error",
                message=f"Error in devlog command for agent {agent_id}: {str(e)}",
                tags=["command", "devlog", "error"]
            )
            await ctx.send(f"Error adding devlog entry: {str(e)}")
            
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