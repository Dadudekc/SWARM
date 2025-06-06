"""
Basic commands cog for Discord bot.
"""

import discord
from discord.ext import commands
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BasicCommands(commands.Cog):
    """Basic commands cog for Discord bot."""
    
    def __init__(self, orchestrator, log_manager):
        """Initialize basic commands cog.
        
        Args:
            orchestrator: System orchestrator instance
            log_manager: Log manager instance
        """
        self.orchestrator = orchestrator
        self.log_manager = log_manager
        self.logger = logging.getLogger(__name__)
    
    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context, command: Optional[str] = None):
        """Show help information.
        
        Args:
            ctx: Command context
            command: Optional command name to get help for
        """
        try:
            if command:
                # Get help for specific command
                cmd = self.bot.get_command(command)
                if not cmd:
                    await ctx.send(f"Command '{command}' not found.")
                    return
                
                embed = discord.Embed(
                    title=f"Help: {cmd.name}",
                    description=cmd.help or "No description available.",
                    color=discord.Color.blue()
                )
                
                if cmd.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(cmd.aliases),
                        inline=False
                    )
                
                if cmd.signature:
                    embed.add_field(
                        name="Usage",
                        value=f"!{cmd.name} {cmd.signature}",
                        inline=False
                    )
            else:
                # Show general help menu
                embed = discord.Embed(
                    title="Dream.OS Bot Help",
                    description="Available commands:",
                    color=discord.Color.blue()
                )
                
                for cog_name, cog in self.bot.cogs.items():
                    if cog_name != "HelpMenu":
                        commands_list = []
                        for cmd in cog.get_commands():
                            if not cmd.hidden:
                                commands_list.append(f"!{cmd.name} - {cmd.help or 'No description'}")
                        
                        if commands_list:
                            embed.add_field(
                                name=cog_name,
                                value="\n".join(commands_list),
                                inline=False
                            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in help command: {e}")
            await ctx.send("An error occurred while fetching help information.")
    
    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """Show system status."""
        try:
            status = await self.orchestrator.get_status()
            
            embed = discord.Embed(
                title="Dream.OS System Status",
                color=discord.Color.green()
            )
            
            # Add system status
            embed.add_field(
                name="System Status",
                value=status.get("status", "Unknown"),
                inline=True
            )
            
            # Add component status
            components = status.get("components", {})
            for name, comp_status in components.items():
                embed.add_field(
                    name=name,
                    value=comp_status,
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await ctx.send("An error occurred while fetching system status.")
    
    @commands.command(name="task")
    async def task(self, ctx: commands.Context, task_name: str, *args):
        """Execute a system task.
        
        Args:
            ctx: Command context
            task_name: Name of task to execute
            *args: Additional task arguments
        """
        try:
            result = await self.orchestrator.execute_task(task_name, *args)
            
            embed = discord.Embed(
                title=f"Task: {task_name}",
                description=result.get("message", "Task completed"),
                color=discord.Color.blue()
            )
            
            if "details" in result:
                embed.add_field(
                    name="Details",
                    value=result["details"],
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in task command: {e}")
            await ctx.send(f"Error executing task '{task_name}': {str(e)}")
    
    @commands.command(name="devlog")
    async def devlog(self, ctx: commands.Context, level: str = "info", *, message: str):
        """Log a development message.
        
        Args:
            ctx: Command context
            level: Log level (debug, info, warning, error)
            message: Message to log
        """
        try:
            # Map level to LogLevel enum
            level_map = {
                "debug": "DEBUG",
                "info": "INFO",
                "warning": "WARNING",
                "error": "ERROR"
            }
            
            log_level = level_map.get(level.lower(), "INFO")
            
            # Log the message
            self.log_manager.log(
                level=log_level,
                platform="discord",
                status="info",
                message=message,
                tags=["devlog", level.lower()]
            )
            
            await ctx.send(f"Logged {level} message: {message}")
            
        except Exception as e:
            self.logger.error(f"Error in devlog command: {e}")
            await ctx.send("An error occurred while logging the message.")

async def setup(bot: commands.Bot):
    """Add the basic commands cog to the bot."""
    await bot.add_cog(BasicCommands(bot.orchestrator, bot.log_manager))

