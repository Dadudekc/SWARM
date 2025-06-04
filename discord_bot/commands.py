"""
Discord Bot Commands

Implements commands for controlling agents via Discord.
"""

import discord
from discord.ext import commands
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

from dreamos.core.messaging.message import Message, MessageMode
from dreamos.core.messaging.message_processor import MessageProcessor
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.agent_interface import AgentInterface
from dreamos.core.metrics import CommandMetrics
from dreamos.core.log_manager import LogManager
from dreamos.core.agent_control.devlog_manager import DevLogManager

logger = logging.getLogger('discord_bot')

class HelpMenu(discord.ui.View):
    """Help menu view for displaying command documentation."""
    
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout
        self.current_page = 0
        self.pages = []
        self.setup_pages()
        self.setup_buttons()
    
    def setup_pages(self):
        self.pages = [
            discord.Embed(
                title="Agent Commands",
                description="Commands for managing agents",
                color=discord.Color.blue()
            ),
            discord.Embed(
                title="DevLog Commands",
                description="Commands for managing agent devlogs",
                color=discord.Color.green()
            ),
            discord.Embed(
                title="System Commands",
                description="Commands for system operations",
                color=discord.Color.red()
            ),
            discord.Embed(
                title="Channel Commands",
                description="Commands for managing channels",
                color=discord.Color.gold()
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
            ("Agent Commands", 0, discord.ButtonStyle.primary),
            ("DevLog Commands", 1, discord.ButtonStyle.success),
            ("System Commands", 2, discord.ButtonStyle.danger),
            ("Channel Commands", 3, discord.ButtonStyle.secondary)
        ]
        
        # Split buttons into two rows
        for i, (label, page_idx, style) in enumerate(categories):
            button = discord.ui.Button(
                label=label,
                style=style,
                row=i // 2  # First 2 buttons in row 0, last 2 in row 1
            )
            # Create a proper callback method that captures page_idx
            async def category_button_callback(interaction: discord.Interaction, p_idx=page_idx):
                await self.show_page(p_idx, interaction)
            button.callback = category_button_callback
            self.add_item(button)

    def add_navigation_buttons(self):
        # Add navigation buttons in a separate row
        prev_button = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)

        next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

        # Add search button in the same row
        search_button = discord.ui.Button(
            label="Search",
            style=discord.ButtonStyle.success,
            row=2
        )
        search_button.callback = self.search_commands
        self.add_item(search_button)

    async def show_page(self, page: int, interaction: discord.Interaction):
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
        
    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to previous page."""
        self.current_page = (self.current_page - 1) % len(self.pages)
        await self.update_page(interaction)
        
    async def next_page(self, interaction: discord.Interaction):
        """Navigate to next page."""
        self.current_page = (self.current_page + 1) % len(self.pages)
        await self.update_page(interaction)
        
    async def search_commands(self, interaction: discord.Interaction):
        """Open command search modal."""
        modal = CommandSearchModal(self)
        await interaction.response.send_modal(modal)
        
    async def update_page(self, interaction: discord.Interaction):
        """Update the help menu page with enhanced visual design."""
        page = self.pages[self.current_page]
        
        embed = discord.Embed(
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

    async def search(self, query: str, interaction: discord.Interaction):
        """Search for commands matching the query."""
        query = query.lower()
        results = []
        
        for page in self.pages:
            for field in page.fields:
                if query in field.name.lower() or query in field.value.lower():
                    results.append(field)
        
        if results:
            embed = discord.Embed(
                title="🔍 Command Search Results",
                description=f"Found {len(results)} matching commands",
                color=discord.Color.blue()
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
    
    async def select_category(self, category: str, interaction: discord.Interaction):
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


class AgentCommands(commands.Cog):
    """Handles agent-related commands."""
    
    def __init__(self, bot):
        """Initialize the commands.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.devlog_manager = DevLogManager()
        self.message_processor = MessageProcessor()
        self.cell_phone = CellPhone()
        self.agent_interface = AgentInterface()
        self.metrics = CommandMetrics()
        self.log_manager = LogManager()  # Initialize LogManager
    
    async def send_command(self, mode: MessageMode, agent_id: str, content: str) -> bool:
        """Send a command to an agent."""
        try:
            message = Message(
                from_agent="Discord",
                to_agent=agent_id,
                content=content,
                mode=mode.value if hasattr(mode, 'value') else mode,
                priority=0,
                timestamp=datetime.now(),
                status="queued"
            )
            return await self.message_processor.process_message(message)
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    @commands.command(name="help")
    async def show_help(self, ctx):
        """Show the help menu."""
        try:
            menu = HelpMenu()
            await ctx.send(embed=menu.pages[0], view=menu)
        except Exception as e:
            await ctx.send(f"Error showing help menu: {str(e)}")
    
    @commands.command(name="list_agents")
    async def list_agents(self, ctx):
        """List all available agents."""
        try:
            agents = ["Agent-1", "Agent-2"]  # Mock data
            if not agents:
                await ctx.send("No agents found.")
                return
                
            embed = discord.Embed(
                title="Available Agents",
                description="List of all registered agents",
                color=discord.Color.blue()
            )
            
            for agent in agents:
                embed.add_field(
                    name=agent,
                    value="Status: Active",
                    inline=False
                )
                
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error listing agents: {str(e)}")
    
    @commands.command(name="list_channels")
    async def list_channels(self, ctx):
        """List all available channels."""
        try:
            channels = ["#general", "#commands"]  # Mock data
            if not channels:
                await ctx.send("No channels found.")
                return
                
            embed = discord.Embed(
                title="Channel Assignments",
                description="List of all registered channels",
                color=discord.Color.blue()
            )
            
            for channel in channels:
                embed.add_field(
                    name=channel,
                    value="Type: Text",
                    inline=False
                )
                
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error listing channels: {str(e)}")
    
    @commands.command(name="send_prompt")
    async def send_prompt(self, ctx, agent_id: str, prompt_text: str):
        """Send a prompt to an agent."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            if not prompt_text:
                await ctx.send("Prompt text is required.")
                return
                
            success = await self.send_command(MessageMode.NORMAL, agent_id, prompt_text)
            if success:
                await ctx.send("Prompt sent")
            else:
                await ctx.send("Failed to send prompt")
        except Exception as e:
            await ctx.send(f"Error sending prompt: {str(e)}")
    
    @commands.command(name="update_devlog")
    async def update_devlog(self, ctx, agent_id: str, message: str):
        """Update the development log."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            if not message:
                await ctx.send("Message is required.")
                return
                
            success = await self.devlog_manager.add_entry(agent_id, message, source="manual")
            if success:
                await ctx.send("Devlog updated")
            else:
                await ctx.send("Failed to update devlog")
        except Exception as e:
            await ctx.send(f"Failed to update devlog: {str(e)}")
    
    @commands.command(name="view_devlog")
    async def view_devlog(self, ctx, agent_id: str):
        """View an agent's devlog."""
        try:
            devlog_content = await self.devlog_manager.get_log(agent_id)
            if not devlog_content:
                await ctx.send(f"No devlog found for agent {agent_id}.")
                return

            # Create a file with the devlog content
            filename = f"{agent_id}_devlog.md"
            file = discord.File(
                io.StringIO(devlog_content),
                filename=filename
            )
            await ctx.send(f"Devlog for agent {agent_id}:", file=file)
        except Exception as e:
            logger.error(f"Error viewing devlog for agent {agent_id}: {str(e)}")
            await ctx.send(f"Error viewing devlog for agent {agent_id}: {str(e)}")
    
    @commands.command(name="clear_devlog")
    async def clear_devlog(self, ctx, agent_id: str):
        """Clear an agent's development log."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.devlog_manager.clear_log(agent_id)
            if success:
                await ctx.send("Devlog cleared")
            else:
                await ctx.send("Failed to clear devlog")
        except Exception as e:
            await ctx.send(f"Failed to clear devlog: {str(e)}")
    
    @commands.command(name="resume_agent")
    async def resume_agent(self, ctx, agent_id: str):
        """Resume an agent's operation."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.send_command(MessageMode.RESUME, agent_id, "Resume operation")
            if success:
                await ctx.send("Successfully resumed")
            else:
                await ctx.send("Failed to resume agent")
        except Exception as e:
            await ctx.send(f"Error resuming agent: {str(e)}")
    
    @commands.command(name="verify_agent")
    async def verify_agent(self, ctx, agent_id: str):
        """Verify an agent's state."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.send_command(MessageMode.VERIFY, agent_id, "Verify state")
            if success:
                await ctx.send("Verification request sent")
            else:
                await ctx.send("Failed to verify agent")
        except Exception as e:
            await ctx.send(f"Error verifying agent: {str(e)}")
    
    @commands.command(name="send_message")
    async def send_message(self, ctx, agent_id: str, message: str):
        """Send a message to an agent."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            if not message:
                await ctx.send("Message is required.")
                return
                
            success = await self.send_command(MessageMode.NORMAL, agent_id, message)
            if success:
                await ctx.send("Message sent")
            else:
                await ctx.send("Failed to send message")
        except Exception as e:
            await ctx.send(f"Error sending message: {str(e)}")
    
    @commands.command(name="restore_agent")
    async def restore_agent(self, ctx, agent_id: str):
        """Restore an agent's state."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.send_command(MessageMode.RESTORE, agent_id, "Restore state")
            if success:
                await ctx.send("Restore request sent")
            else:
                await ctx.send("Failed to restore agent")
        except Exception as e:
            await ctx.send(f"Error restoring agent: {str(e)}")
    
    @commands.command(name="sync_agent")
    async def sync_agent(self, ctx, agent_id: str):
        """Synchronize an agent's state."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.send_command(MessageMode.SYNC, agent_id, "Sync state")
            if success:
                await ctx.send("Sync request sent")
            else:
                await ctx.send("Failed to sync agent")
        except Exception as e:
            await ctx.send(f"Error synchronizing agent: {str(e)}")
    
    @commands.command(name="cleanup_agent")
    async def cleanup_agent(self, ctx, agent_id: str):
        """Clean up an agent's resources."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            success = await self.send_command(MessageMode.CLEANUP, agent_id, "Cleanup resources")
            if success:
                await ctx.send("Cleanup request sent")
            else:
                await ctx.send("Failed to cleanup agent")
        except Exception as e:
            await ctx.send(f"Error cleaning up agent: {str(e)}")
    
    @commands.command(name="multi_command")
    async def multi_command(self, ctx, agent_id: str, command: str):
        """Execute a command on multiple agents."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            if not command:
                await ctx.send("Command is required.")
                return
                
            success = await self.send_command(MessageMode.NORMAL, agent_id, command)
            if success:
                await ctx.send("Multi-command sent")
            else:
                await ctx.send("Failed to execute multi-command")
        except Exception as e:
            await ctx.send(f"Error executing multi-command: {str(e)}")
    
    @commands.command(name="system_command")
    async def system_command(self, ctx, agent_id: str, command: str):
        """Send a system command to an agent."""
        try:
            logger.debug(f"Starting system_command for agent {agent_id} with command: {command}")
            
            if not agent_id or not command:
                logger.debug("Missing agent_id or command")
                await ctx.send("Both agent ID and command are required.")
                return

            logger.debug(f"Calling send_command with MessageMode.SYSTEM")
            success = await self.send_command(MessageMode.SYSTEM, agent_id, command)
            logger.debug(f"send_command returned: {success}")
            
            if success:
                logger.debug("Command successful, sending success message")
                await ctx.send(f"System command sent to agent {agent_id}.")
            else:
                logger.debug("Command failed, sending error message")
                await ctx.send(f"Error executing system command for agent {agent_id}.")
        except Exception as e:
            logger.error(f"Error in system command for agent {agent_id}: {str(e)}", exc_info=True)
            await ctx.send(f"Error executing system command: {str(e)}")
    
    @commands.command(name="assign_channel")
    async def assign_channel(self, ctx, agent_id: str, channel_id: str):
        """Assign a channel to an agent."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
                
            if not channel_id:
                await ctx.send("Channel ID is required.")
                return
                
            # Use proper config path
            config_path = Path("config/agent_config.yaml")
            if not config_path.exists():
                # Create config directory if it doesn't exist
                config_path.parent.mkdir(parents=True, exist_ok=True)
                # Create initial config
                config = {
                    "log_dir": "logs",
                    "channel_assignments": {},
                    "global_ui": {
                        "input_box": {"x": 100, "y": 100},
                        "initial_spot": {"x": 200, "y": 200},
                        "copy_button": {"x": 300, "y": 300},
                        "response_region": {
                            "top_left": {"x": 400, "y": 400},
                            "bottom_right": {"x": 600, "y": 600}
                        }
                    }
                }
            else:
                # Load existing config
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
            
            # Ensure channel_assignments exists
            if "channel_assignments" not in config:
                config["channel_assignments"] = {}
            
            # Update assignment
            config["channel_assignments"][agent_id] = channel_id
            
            # Save config
            with open(config_path, "w") as f:
                yaml.dump(config, f)
            
            await ctx.send(f"✅ Channel {channel_id} assigned to {agent_id}")
        except Exception as e:
            logger.error(f"Error assigning channel: {e}")
            await ctx.send(f"❌ Error assigning channel: {str(e)}")
    
    @commands.command(name="logs")
    async def show_logs(self, ctx, agent_id: str = None, level: str = "info", limit: int = 10):
        """Show logs for an agent or all agents.
        
        Args:
            agent_id: Optional agent ID to filter logs
            level: Log level (info, warning, error, debug)
            limit: Maximum number of logs to show
        """
        try:
            # Get logs from LogManager
            logs = self.log_manager.read_logs(
                platform=agent_id or "all",
                level=level.upper(),
                limit=limit
            )
            
            if not logs:
                await ctx.send(f"No {level} logs found for {agent_id or 'all agents'}")
                return
            
            # Create embed for logs
            embed = discord.Embed(
                title=f"Logs for {agent_id or 'All Agents'}",
                description=f"Showing {len(logs)} {level} logs",
                color=discord.Color.blue()
            )
            
            # Add log entries to embed
            for log in logs:
                timestamp = log.get('timestamp', 'Unknown')
                message = log.get('message', 'No message')
                status = log.get('status', 'Unknown')
                
                embed.add_field(
                    name=f"{timestamp} - {status}",
                    value=message,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
            # Log the command usage
            self.log_manager.info(
                platform="discord",
                status="command",
                message=f"Logs command used for {agent_id or 'all agents'}",
                metadata={
                    "user": str(ctx.author),
                    "level": level,
                    "limit": limit
                }
            )
            
        except Exception as e:
            error_msg = f"Error showing logs: {str(e)}"
            await ctx.send(error_msg)
            
            # Log the error
            self.log_manager.error(
                platform="discord",
                status="error",
                message="Error in logs command",
                error=str(e),
                metadata={
                    "user": str(ctx.author),
                    "agent_id": agent_id,
                    "level": level
                }
            )

    def cog_unload(self):
        """Clean up resources."""
        self.message_processor.shutdown()
        self.cell_phone.shutdown()

async def setup(bot):
    """Set up the commands cog."""
    await bot.add_cog(AgentCommands(bot)) 