"""
Basic commands for the Discord bot.
"""

from tests.utils.mock_discord import Embed, Color, Interaction
from discord_bot.help_menu import HelpMenu
import logging

logger = logging.getLogger('discord_bot')

class BasicCommands:
    """Basic command handlers for the Discord bot."""
    
    def __init__(self, bot):
        """Initialize basic commands.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
    
    async def help_command(self, interaction: Interaction):
        """Show help menu.
        
        Args:
            interaction: Discord interaction
        """
        help_menu = HelpMenu()
        await interaction.response.send_message(
            embed=help_menu.pages[0],
            view=help_menu
        )
    
    async def ping_command(self, interaction: Interaction):
        """Check bot latency.
        
        Args:
            interaction: Discord interaction
        """
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! Latency: {latency}ms"
        )
    
    async def about_command(self, interaction: Interaction):
        """Show bot information.
        
        Args:
            interaction: Discord interaction
        """
        embed = Embed(
            title="About Dream.OS",
            description="An intelligent operating system for Discord",
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
        
        embed.add_field(
            name="GitHub",
            value="[Repository](https://github.com/dreamos/dreamos)",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

