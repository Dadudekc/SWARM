"""
Discord Bot Commands

Implements commands for controlling agents via Discord.
"""

from tests.utils.mock_discord import (
    commands,
    ui,
    Embed,
    Color,
    ButtonStyle,
    Interaction
)
import logging
from typing import Optional, Dict, List
import asyncio
from datetime import datetime
import os
import json
import time
import yaml

import io
from pathlib import Path

from dreamos.core.messaging.common import Message
from dreamos.core.messaging.message_processor import MessageProcessor
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.enums import MessageMode
from dreamos.core.agent_interface import AgentInterface
from dreamos.core.metrics import CommandMetrics
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel
from dreamos.core.autonomy.error import ErrorTracker, ErrorHandler, ErrorSeverity

logger = logging.getLogger('discord_bot')

class HelpMenu(ui.View):
    """Help menu view for displaying command documentation."""
    
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout
        self.current_page = 0
        self.pages = []
        self.setup_pages()
        self.setup_buttons()
    
    def setup_pages(self):
        self.pages = [
            Embed(
                title="Agent Commands",
                description="Commands for managing agents",
                color=Color.blue()
            ),
            Embed(
                title="DevLog Commands",
                description="Commands for managing agent devlogs",
                color=Color.green()
            ),
            Embed(
                title="System Commands",
                description="Commands for system operations",
                color=Color.red()
            ),
            Embed(
                title="Channel Commands",
                description="Commands for managing channels",
                color=Color.gold()
            )
        ]
        
        # Add fields to pages
        self.pages[0].add_field(
            name="/list",
            value="List available agents",
            inline=False
        )
        self.pages[0].add_field(
            name="/prompt <agent> <text>",
            value="Send a prompt to an agent",
            inline=False
        )
        self.pages[0].add_field(
            name="/message <agent> <text>",
            value="Send a message to an agent",
            inline=False
        )
        
        self.pages[1].add_field(
            name="/devlog <agent> <text>",
            value="Update an agent's devlog",
            inline=False
        )
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
        
        self.pages[2].add_field(
            name="/resume <agent>",
            value="Resume an agent",
            inline=False
        )
        self.pages[2].add_field(
            name="/verify <agent>",
            value="Verify an agent's state",
            inline=False
        )
        self.pages[2].add_field(
            name="/restore <agent>",
            value="Restore an agent's state",
            inline=False
        )
        self.pages[2].add_field(
            name="/sync <agent>",
            value="Sync an agent's state",
            inline=False
        )
        self.pages[2].add_field(
            name="/cleanup <agent>",
            value="Clean up an agent's resources",
            inline=False
        )
        
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

    def setup_buttons(self):
        self.add_category_buttons()
        self.add_navigation_buttons()

    def add_category_buttons(self):
        categories = [
            ("Agent Commands", 0, ButtonStyle.primary),
            ("DevLog Commands", 1, ButtonStyle.success),
            ("System Commands", 2, ButtonStyle.danger),
            ("Channel Commands", 3, ButtonStyle.secondary)
        ]
        
        # Split buttons into two rows
        for i, (label, page_idx, style) in enumerate(categories):
            button = ui.Button(
                label=label,
                style=style,
                row=i // 2  # First 2 buttons in row 0, last 2 in row 1
            )
            # Create a proper callback method that captures page_idx
            async def category_button_callback(interaction: Interaction, p_idx=page_idx):
                await self.show_page(p_idx, interaction)
            button.callback = category_button_callback
            self.add_item(button)

    def add_navigation_buttons(self):
        # Add navigation buttons in a separate row
        prev_button = ui.Button(
            label="Previous",
            style=ButtonStyle.secondary,
            row=2
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)

        next_button = ui.Button(
            label="Next",
            style=ButtonStyle.secondary,
            row=2
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

        # Add search button in the same row
        search_button = ui.Button(
            label="Search",
            style=ButtonStyle.success,
            row=2
        )
        search_button.callback = self.search_commands
        self.add_item(search_button)

    async def show_page(self, page: int, interaction: Interaction):
        """Show specific page."""
        self.current_page = page
        if interaction: # Make sure interaction is not None
            await self.update_page(interaction)
        else:
            # This case should ideally not happen if callbacks are set up correctly
            # Log or handle the absence of interaction if necessary
            logger.warn("HelpMenu.show_page called without interaction object.")
            # Potentially, if there's a way to get the last interaction or a default one for the view:
            # await self.update_page(self.last_interaction_or_ctx_placeholder)
            pass # Or decide not to update if no interaction
        
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
        
    async def update_page(self, interaction: Interaction):
        """Update the help menu page with enhanced visual design."""
        page = self.pages[self.current_page]
        
        embed = Embed(
            title=page.title,
            description=page.description,
            color=page.color
        )
        
        # Add animated header with custom image
        embed.set_author(
            name="Dream.OS Swarm Command Interface",
            icon_url="https://i.imgur.com/your-swarm-icon.png",
            url="https://github.com/Dadudekc/SWARM"
        )
        
        # Add thumbnail if available
        if hasattr(page, 'thumbnail') and page.thumbnail:
            embed.set_thumbnail(url=page.thumbnail.url)
        
        # Add command fields with enhanced formatting and syntax highlighting
        for field in page.fields:
            embed.add_field(
                name=f"```ansi\n{field.name}\n```",
                value=f"```md\n{field.value}\n```",
                inline=field.inline
            )
            
        # Add interactive footer with dynamic content
        embed.set_footer(
            text=f"Swarm Intelligence • Page {self.current_page + 1}/{len(self.pages)} • Type !swarm_help for more info",
            icon_url="https://i.imgur.com/your-swarm-icon.png"
        )
        
        # Add timestamp for dynamic feel
        embed.timestamp = datetime.now()
        
        # Add a subtle border effect
        embed.set_image(url="https://i.imgur.com/your-border-image.png")  # Add your border image URL
        
        await interaction.response.edit_message(embed=embed, view=self)

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
            "agent": 0,  # Agent management commands
            "devlog": 1,  # Devlog commands
            "state": 2,  # State management commands
            "stats": 3   # Statistics commands
        }
        
        if category in category_pages:
            await self.show_page(category_pages[category], interaction)
        else:
            await interaction.response.send_message(
                f"Invalid category. Available categories: {', '.join(category_pages.keys())}",
                ephemeral=True
            )

class CommandSearchModal(ui.Modal, title="🔍 Search Commands"):
    """Modal for searching commands with enhanced UI."""
    
    def __init__(self, help_menu: HelpMenu):
        super().__init__()
        self.help_menu = help_menu
        self.search_input = ui.TextInput(
            label="Enter command or keyword",
            placeholder="e.g., status, task, gui",
            required=True,
            min_length=1,
            max_length=50,
            style=ui.TextStyle.paragraph
        )
        self.add_item(self.search_input)
        
    async def on_submit(self, interaction: Interaction):
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
            embed = Embed(
                title="🔍 Command Search Results",
                description=f"Found {len(results)} matches for '{query}'",
                color=Color.blue()
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
            embed = Embed(
                title="❌ No Results Found",
                description=f"No commands found matching '{query}'",
                color=Color.red()
            )
            embed.add_field(
                name="💡 Suggestions",
                value="• Check your spelling\n• Try a more general term\n• Browse categories using the buttons below",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class AgentCommands(commands.Cog):
    """Commands for managing agents."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_processor = MessageProcessor()
        self.log_manager = LogManager()
        self.MessageMode = MessageMode
        
        # Initialize error handling
        self.error_tracker = ErrorTracker()
        self.error_handler = ErrorHandler(self.error_tracker)
        
        # Load configuration
        self._load_config()
        
        # Initialize metrics
        self.metrics = CommandMetrics()
        
        # Register commands
        self.show_help = commands.command(name="help")(self.show_help)
        self.list_agents = commands.command(name="list")(self.list_agents)
        self.send_prompt = commands.command(name="prompt")(self.send_prompt)
        self.update_log = commands.command(name="devlog")(self.update_log)
        self.view_log = commands.command(name="viewlog")(self.view_log)
        self.clear_log = commands.command(name="clearlog")(self.clear_log)
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            config_path = Path("config/discord_bot.yaml")
            if config_path.exists():
                with open(config_path) as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = {}
                
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.HIGH,
                agent_id="discord_bot",
                context={"operation": "load_config"}
            )
            logger.error(f"Error loading config: {e}")
            self.config = {}
    
    async def send_command(self, mode: MessageMode, agent_id: str, content: str) -> bool:
        """Send a command to an agent."""
        try:
            message = Message(
                mode=mode,
                agent_id=agent_id,
                content=content,
                timestamp=datetime.now()
            )
            
            # Send with retry
            return await self.error_handler.with_retry(
                operation="send_command",
                agent_id=agent_id,
                func=self.message_processor.process_message,
                message=message
            )
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.HIGH,
                agent_id=agent_id,
                context={
                    "operation": "send_command",
                    "mode": mode,
                    "content": content
                }
            )
            logger.error(f"Error sending command: {e}")
            return False
    
    async def show_help(self, ctx):
        """Show help menu."""
        try:
            view = HelpMenu()
            await ctx.send(embed=view.pages[0], view=view)
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id="discord_bot",
                context={"operation": "show_help"}
            )
            await ctx.send("Error showing help menu. Please try again later.")
    
    async def list_agents(self, ctx):
        """List available agents."""
        try:
            embed = Embed(
                title="Available Agents",
                description="List of active agents in the system",
                color=Color.blue()
            )
            
            # Get agent list from bot
            agents = self.bot.agent_resume.coords.keys()
            
            for agent in agents:
                embed.add_field(
                    name=agent,
                    value="Active",
                    inline=True
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id="discord_bot",
                context={"operation": "list_agents"}
            )
            await ctx.send("Error listing agents. Please try again later.")
    
    async def send_prompt(self, ctx, agent_id: str, prompt_text: str):
        """Send a prompt to an agent."""
        try:
            success = await self.send_command(MessageMode.PROMPT, agent_id, prompt_text)
            if success:
                await ctx.send(f"Prompt sent to {agent_id}")
            else:
                await ctx.send(f"Failed to send prompt to {agent_id}")
                
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.HIGH,
                agent_id=agent_id,
                context={
                    "operation": "send_prompt",
                    "prompt_text": prompt_text
                }
            )
            await ctx.send(f"Error sending prompt to {agent_id}. Please try again later.")
    
    async def update_log(self, ctx, agent_id: str, message: str):
        """Update agent log."""
        try:
            success = await self.error_handler.with_retry(
                operation="update_log",
                agent_id=agent_id,
                func=self.log_manager.log,
                message=message,
                level=LogLevel.INFO
            )
            
            if success:
                await ctx.send(f"Log updated for {agent_id}")
            else:
                await ctx.send(f"Failed to update log for {agent_id}")
                
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=agent_id,
                context={
                    "operation": "update_log",
                    "message": message
                }
            )
            await ctx.send(f"Error updating log for {agent_id}. Please try again later.")
    
    async def view_log(self, ctx, agent_id: str):
        """View agent log."""
        try:
            log_entries = await self.error_handler.with_retry(
                operation="view_log",
                agent_id=agent_id,
                func=self.log_manager.read_logs,
                platform=agent_id
            )
            
            if log_entries:
                # Format log entries
                log_content = "\n".join([
                    f"[{entry['timestamp']}] {entry['level']}: {entry['message']}"
                    for entry in log_entries
                ])
                await ctx.send(f"Log for {agent_id}:\n```\n{log_content}\n```")
            else:
                await ctx.send(f"No log found for {agent_id}")
                
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=agent_id,
                context={"operation": "view_log"}
            )
            await ctx.send(f"Error viewing log for {agent_id}. Please try again later.")
    
    async def clear_log(self, ctx, agent_id: str):
        """Clear agent log."""
        try:
            rotated_path = await self.error_handler.with_retry(
                operation="clear_log",
                agent_id=agent_id,
                func=self.log_manager.rotate,
                platform=agent_id
            )
            
            if rotated_path:
                await ctx.send(f"Log cleared for {agent_id}")
            else:
                await ctx.send(f"Failed to clear log for {agent_id}")
                
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=agent_id,
                context={"operation": "clear_log"}
            )
            await ctx.send(f"Error clearing log for {agent_id}. Please try again later.")

async def setup(bot):
    """Set up the commands cog."""
    await bot.add_cog(AgentCommands(bot)) 