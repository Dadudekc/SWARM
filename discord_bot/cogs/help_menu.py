"""
Help menu cog for Discord bot.
"""

from tests.utils.mock_discord import (
    commands,
    Embed,
    Color
)
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class HelpMenu(commands.Cog):
    """Help menu cog for Discord bot."""
    
    def __init__(self, bot):
        """Initialize help menu cog.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
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
                
                embed = Embed(
                    title=f"Help: {cmd.name}",
                    description=cmd.help or "No description available.",
                    color=Color.blue()
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
                embed = Embed(
                    title="Dream.OS Bot Help",
                    description="Available commands:",
                    color=Color.blue()
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
    
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check bot latency."""
        try:
            latency = round(self.bot.latency * 1000)
            await ctx.send(f"Pong! Latency: {latency}ms")
        except Exception as e:
            self.logger.error(f"Error in ping command: {e}")
            await ctx.send("An error occurred while checking latency.")
    
    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        """Show system status."""
        try:
            status = await self.bot.orchestrator.get_status()
            
            embed = Embed(
                title="Dream.OS System Status",
                color=Color.green()
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
    
    @commands.command(name="about")
    async def about(self, ctx: commands.Context):
        """Show information about the bot."""
        try:
            embed = Embed(
                title="Dream.OS Bot",
                description="A Discord bot for interacting with the Dream.OS system.",
                color=Color.blue()
            )
            
            embed.add_field(
                name="Version",
                value="1.0.0",
                inline=True
            )
            
            embed.add_field(
                name="Author",
                value="Dream.OS Team",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in about command: {e}")
            await ctx.send("An error occurred while fetching bot information.")

async def setup(bot: commands.Bot):
    """Add the help menu cog to the bot."""
    await bot.add_cog(HelpMenu(bot)) 
