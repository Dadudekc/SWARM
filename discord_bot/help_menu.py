"""Help menu and search modal for Discord commands."""
from tests.utils.mock_discord import ui, Embed, Color, ButtonStyle, Interaction
import logging
from datetime import datetime
import discord
from typing import Optional, Dict, Any

logger = logging.getLogger('discord_bot')

class HelpMenu(ui.View):
    """Interactive help menu for Discord bot commands."""
    
    def __init__(self):
        """Initialize help menu."""
        super().__init__(timeout=180)
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
        # Category buttons
        self.add_item(ui.Button(
            label="Agents",
            style=ButtonStyle.primary,
            custom_id="agents",
            row=0
        ))
        self.add_item(ui.Button(
            label="DevLogs",
            style=ButtonStyle.success,
            custom_id="devlogs",
            row=0
        ))
        self.add_item(ui.Button(
            label="System",
            style=ButtonStyle.danger,
            custom_id="system",
            row=0
        ))
        self.add_item(ui.Button(
            label="Channels",
            style=ButtonStyle.secondary,
            custom_id="channels",
            row=0
        ))
        
        # Navigation buttons
        self.add_item(ui.Button(
            label="Previous",
            style=ButtonStyle.secondary,
            custom_id="prev",
            row=1
        ))
        self.add_item(ui.Button(
            label="Search",
            style=ButtonStyle.primary,
            custom_id="search",
            row=1
        ))
        self.add_item(ui.Button(
            label="Next",
            style=ButtonStyle.secondary,
            custom_id="next",
            row=1
        ))
    
    async def search_commands(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for commands matching query.
        
        Args:
            query: Search query string
            
        Returns:
            Dict containing command info if found, None otherwise
        """
        query = query.lower()
        for cmd_name, cmd_info in self.command_cache.items():
            if query in cmd_name.lower() or query in cmd_info['value'].lower():
                return cmd_info
        return None
    
    async def show_page(self, page: int, interaction: Interaction):
        """Show specific page.
        
        Args:
            page: Page number to show
            interaction: Discord interaction object
        """
        if not 0 <= page < len(self.pages):
            await interaction.response.send_message(
                "Invalid page number",
                ephemeral=True
            )
            return
            
        self.current_page = page
        await self.update_page(interaction)
    
    async def update_page(self, interaction: Interaction):
        """Update current page.
        
        Args:
            interaction: Discord interaction object
        """
        try:
            await interaction.response.edit_message(
                embed=self.pages[self.current_page],
                view=self
            )
        except Exception as e:
            logger.error(f"Error updating help menu page: {e}")
            await interaction.response.send_message(
                "Error updating help menu",
                ephemeral=True
            )

class CommandSearchModal(discord.ui.Modal, title="🔍 Search Commands"):
    """Modal for searching commands with enhanced UI."""
    
    def __init__(self, help_menu: HelpMenu):
        super().__init__()
        self.help_menu = help_menu
        self.search_input = discord.ui.TextInput(
            label="Enter command or keyword",
            placeholder="e.g., status, task, gui",
            required=True,
            min_length=1,
            max_length=50,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.search_input)
        
    async def on_submit(self, interaction: discord.Interaction):
        """Handle search submission with enhanced results display."""
        query = self.search_input.value.lower()
        results = []
        
        # Search through all pages with fuzzy matching
        for page in self.help_menu.pages:
            for name, value in page["fields"]:
                if query in name.lower() or query in value.lower():
                    results.append((name, value, page["title"], page["icon"]))
        
        if results:
            # Create results embed with enhanced styling
            embed = discord.Embed(
                title="🔍 Command Search Results",
                description=f"Found {len(results)} matches for '{query}'",
                color=discord.Color.blue()
            )
            
            # Group results by category
            categories = {}
            for name, value, category, icon in results[:10]:
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, value))
            
            # Add grouped results to embed
            for category, commands in categories.items():
                category_text = ""
                for name, value in commands:
                    category_text += f"**{name}**\n{value}\n\n"
                embed.add_field(
                    name=f"{icon} {category}",
                    value=category_text,
                    inline=False
                )
                
            if len(results) > 10:
                embed.set_footer(text=f"Showing 10 of {len(results)} results • Refine your search for more specific results")
                
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            # Enhanced no results message
            embed = discord.Embed(
                title="❌ No Results Found",
                description=f"No commands found matching '{query}'",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 Suggestions",
                value="• Check your spelling\n• Try a more general term\n• Browse categories using the buttons below",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


