"""
Basic Discord bot commands and utilities.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from discord.ext.commands import Context
from social.utils.log_manager import LogManager

# Debug print to check commands.Cog
import discord.ext.commands as real_commands
print("DEBUG: commands.Cog is", getattr(real_commands, 'Cog', None))

# Ensure commands.Cog is properly imported
if not hasattr(commands, 'Cog'):
    commands.Cog = type('Cog', (), {})

class HelpMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        await ctx.send("Available commands: !help, !status, !prompt, ...")

class BasicCog(commands.Cog):
    """Basic bot commands and utilities."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="help")
    async def show_help(self, ctx):
        """Display the help menu."""
        menu = HelpMenu(self.bot)
        await ctx.send(embed=menu.pages[0], view=menu)
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! Latency: {latency}ms")

async def setup(bot):
    """Set up the basic cog."""
    await bot.add_cog(BasicCog(bot))

class BasicCommands(commands.Cog):
    """Group core bot commands into a Cog for easier management."""

    def __init__(self, orchestrator, log_manager: LogManager):
        """Initialize the basic commands cog.
        
        Args:
            orchestrator: System orchestrator instance
            log_manager: Log manager instance
        """
        self.orchestrator = orchestrator
        self.log_manager = log_manager
        super().__init__()

    @commands.command()
    async def help(self, ctx: Context) -> None:
        """Show help information."""
        help_text = (
            "**Dream.OS Bot Commands**\n\n"
            "`!help` - Show this help message\n"
            "`!status <agent_id>` - Show agent status\n"
            "`!task <agent_id> <title> <description>` - Create new task\n"
            "`!devlog <agent_id> <category> <content>` - Add devlog entry"
        )
        await ctx.send(help_text)
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Help command executed by {ctx.author}",
            tags=["command", "help"],
        )

    @commands.command()
    async def status(self, ctx: Context, agent_id: str) -> None:
        """Show agent status."""
        status = await self.orchestrator.get_agent_status(agent_id)
        msg = f"**Status for Agent {agent_id}**\n\n"
        msg += "**Tasks**\n"
        msg += f"Total: {status['tasks']['total']}\n"
        msg += f"Summary: {status['tasks']['summary']}\n\n"
        msg += "**DevLog**\n"
        msg += f"Total Entries: {status['devlog']['total_entries']}\n\n"
        msg += "**Messages**\n"
        msg += f"Total: {status['messages']['total']}\n"
        await ctx.send(msg)
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Status command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "status"],
        )

    @commands.command()
    async def task(
        self, ctx: Context, agent_id: str, title: str, *, description: str
    ) -> None:
        """Create a new task for an agent."""
        task_id = await self.orchestrator.create_agent_task(
            agent_id=agent_id, title=title, description=description
        )
        await ctx.send(f"Task created with ID: {task_id}")
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Task command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "task"],
        )

    @commands.command()
    async def devlog(
        self, ctx: Context, agent_id: str, category: str, *, content: str
    ) -> None:
        """Add a devlog entry for an agent."""
        await self.orchestrator.devlog_manager.add_devlog_entry(
            agent_id=agent_id,
            category=category,
            content=content,
            author=str(ctx.author),
        )
        await ctx.send("Devlog entry added successfully")
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Devlog command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "devlog"],
        )

