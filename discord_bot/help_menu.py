"""
Help menu for Discord bot commands.
"""

from tests.utils.mock_discord import ui, Embed, Color, ButtonStyle, Interaction
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('discord_bot')

class HelpMenu(ui.View):
    """Interactive help menu for Discord bot commands."""
    
    def __init__(self):
        """Initialize help menu."""
        super().__init__(timeout=180)  # 3 minute timeout
        self.current_page = 0
        self.pages = []
        self.command_cache = {}  # Cache for command search
        self.setup_pages()
        self.setup_buttons()
    
    def setup_pages(self):
        """Set up help menu pages."""
        self.pages = [
            Embed(title="Agent Commands", description="Commands for managing agents", color=Color.blue()),
            Embed(title="DevLog Commands", description="Commands for managing agent devlogs", color=Color.green()),
            Embed(title="System Commands", description="Commands for system management", color=Color.orange()),
            Embed(title="Channel Commands", description="Commands for channel management", color=Color.purple())
        ]
        
        # Agent Commands
        self.pages[0].add_field(
            name="/list_agents",
            value="List all available agents",
            inline=False
        )
        self.pages[0].add_field(
            name="/agent_status <agent>",
            value="Show agent status and metrics",
            inline=False
        )
        self.pages[0].add_field(
            name="/send_prompt <agent> <prompt>",
            value="Send a prompt to an agent",
            inline=False
        )
        
        # DevLog Commands
        self.pages[1].add_field(
            name="/viewlog <agent>",
            value="View an agent's devlog",
            inline=False
        )
        self.pages[1].add_field(
            name="/clearlog <agent>",
            value="Clear an agent's devlog",
            inline=False
        )
        self.pages[1].add_field(
            name="/log_level <agent> <level>",
            value="Set agent's log level (DEBUG, INFO, WARNING, ERROR)",
            inline=False
        )
        
        # System Commands
        self.pages[2].add_field(
            name="/system_status",
            value="Show system status and metrics",
            inline=False
        )
        self.pages[2].add_field(
            name="/restart <component>",
            value="Restart a system component",
            inline=False
        )
        self.pages[2].add_field(
            name="/metrics",
            value="Show system metrics",
            inline=False
        )
        
        # Channel Commands
        self.pages[3].add_field(
            name="/channels",
            value="List channel assignments",
            inline=False
        )
        self.pages[3].add_field(
            name="/assign <agent> <channel>",
            value="Assign a channel to an agent",
            inline=False
        )
        self.pages[3].add_field(
            name="/unassign <agent> <channel>",
            value="Remove channel assignment from agent",
            inline=False
        )
        
        # Build command cache for search
        for page in self.pages:
            for field in page.fields:
                cmd_name = field.name.split()[0]  # Extract command name
                self.command_cache[cmd_name] = {
                    'name': field.name,
                    'value': field.value,
                    'page': self.pages.index(page)
                }
    
    def setup_buttons(self):
        """Set up navigation buttons."""
        # Previous button
        self.add_item(ui.Button(
            style=ButtonStyle.primary,
            label="Previous",
            custom_id="prev",
            row=0
        ))
        
        # Next button
        self.add_item(ui.Button(
            style=ButtonStyle.primary,
            label="Next",
            custom_id="next",
            row=0
        ))
        
        # Search button
        self.add_item(ui.Button(
            style=ButtonStyle.secondary,
            label="Search",
            custom_id="search",
            row=0
        ))
    
    async def update_page(self, interaction: Interaction):
        """Update the current page."""
        await interaction.response.edit_message(
            embed=self.pages[self.current_page],
            view=self
        )
    
    async def show_page(self, page: int, interaction: Interaction):
        """Show specific page."""
        self.current_page = page
        await self.update_page(interaction)
    
    async def previous_page(self, interaction: Interaction):
        """Navigate to previous page."""
        self.current_page = (self.current_page - 1) % len(self.pages)
        await self.update_page(interaction)
    
    async def next_page(self, interaction: Interaction):
        """Navigate to next page."""
        self.current_page = (self.current_page + 1) % len(self.pages)
        await self.update_page(interaction)
    
    async def search_commands(self, interaction: Interaction):
        """Open command search modal."""
        modal = CommandSearchModal(self)
        await interaction.response.send_modal(modal)
    
    async def search(self, query: str, interaction: Interaction):
        """Search for commands matching the query."""
        query = query.lower()
        results = []
        
        for page in self.pages:
            for field in page.fields:
                if query in field.name.lower() or query in field.value.lower():
                    results.append(field)
        
        if results:
            embed = Embed(
                title="🔍 Command Search Results",
                description=f"Found {len(results)} matching commands",
                color=Color.blue()
            )
            
            for field in results:
                embed.add_field(
                    name=field.name,
                    value=field.value,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "No commands found matching your search.",
                ephemeral=True
            )
    
    async def select_category(self, category: str, interaction: Interaction):
        """Show commands for a specific category."""
        category = category.lower()
        category_pages = {
            "agent": 0,    # Agent management commands
            "devlog": 1,   # Devlog commands
            "system": 2,   # System commands
            "channel": 3   # Channel commands
        }
        
        if category in category_pages:
            await self.show_page(category_pages[category], interaction)
        else:
            await interaction.response.send_message(
                f"Invalid category. Available categories: {', '.join(category_pages.keys())}",
                ephemeral=True
            )

class CommandSearchModal(ui.Modal):
    """Modal for searching commands."""
    
    def __init__(self, help_menu: HelpMenu):
        """Initialize search modal.
        
        Args:
            help_menu: Parent help menu
        """
        super().__init__(title="Search Commands")
        self.help_menu = help_menu
        
        # Add search input
        self.add_item(ui.TextInput(
            label="Search Query",
            placeholder="Enter command name or description...",
            required=True
        ))
    
    async def on_submit(self, interaction: Interaction):
        """Handle modal submission.
        
        Args:
            interaction: Discord interaction
        """
        query = self.children[0].value
        await self.help_menu.search(query, interaction)


