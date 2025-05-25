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
import aiohttp
import pyautogui
import threading

from dreamos.core.messaging import Message, MessageMode, MessageProcessor
from dreamos.core import CellPhone

logger = logging.getLogger('discord_bot')

class HelpMenu(discord.ui.View):
    """Interactive help menu with buttons and visual effects."""
    
    def __init__(self):
        super().__init__(timeout=180)
        self.current_page = 0
        self.pages = [
            {
                "title": "🔄 Swarm Core Commands",
                "description": "Essential commands for swarm coordination and control",
                "color": discord.Color.purple(),
                "icon": "🔄",
                "thumbnail": "https://i.imgur.com/core-commands.png",  # Add your image URL
                "fields": [
                    ("!swarm_help", "Access the swarm command interface"),
                    ("!list", "Display active swarm members"),
                    ("!agent_status [agent_id]", "Monitor swarm member status\nExample: !agent_status Agent-1"),
                    ("!resume <agent_id>", "Activate swarm member\nExample: !resume Agent-1"),
                    ("!verify <agent_id>", "Validate swarm member integrity\nExample: !verify Agent-1"),
                    ("!message <agent_id> <message>", "Direct swarm communication\nExample: !message Agent-1 Initiate protocol")
                ]
            },
            {
                "title": "🎯 Swarm Task Management",
                "description": "Commands for swarm task distribution and execution",
                "color": discord.Color.blue(),
                "icon": "🎯",
                "fields": [
                    ("!task <agent_ids> <task>", "Distribute task to swarm members\nExample: !task 1,3,5 Execute system analysis"),
                    ("!prompt <agent_id> <prompt>", "Send directive to swarm member\nExample: !prompt Agent-1 Analyze network patterns"),
                    ("!multi <command> <agent_ids>", "Coordinate multiple swarm members\nExample: !multi resume 1,3,5"),
                    ("!broadcast <message>", "Transmit to entire swarm\nExample: !broadcast System-wide protocol update")
                ]
            },
            {
                "title": "⚡ Swarm System Operations",
                "description": "Commands for swarm system maintenance and optimization",
                "color": discord.Color.gold(),
                "icon": "⚡",
                "fields": [
                    ("!system <action>", "Execute swarm-wide operations\nActions: status, sync, backup, cleanup\nExample: !system status"),
                    ("!repair <agent_id>", "Restore swarm member functionality\nExample: !repair Agent-1"),
                    ("!backup <agent_id>", "Preserve swarm member state\nExample: !backup Agent-1"),
                    ("!restore <agent_id>", "Recover swarm member from backup\nExample: !restore Agent-1"),
                    ("!sync <agent_id>", "Synchronize swarm member\nExample: !sync Agent-1"),
                    ("!cleanup <agent_id>", "Optimize swarm member resources\nExample: !cleanup Agent-1")
                ]
            },
            {
                "title": "📊 Swarm Intelligence",
                "description": "Commands for swarm knowledge and development tracking",
                "color": discord.Color.green(),
                "icon": "📊",
                "fields": [
                    ("!devlog <agent_id> <message>", "Record swarm member development\nExample: !devlog Agent-1 Protocol optimization complete"),
                    ("!view_devlog <agent_id>", "View swarm member development log\nExample: !view_devlog Agent-1"),
                    ("!clear_devlog <agent_id>", "Reset swarm member development log\nExample: !clear_devlog Agent-1"),
                    ("!devlog_channel", "Configure swarm intelligence channel"),
                    ("!channels", "Display swarm communication channels")
                ]
            },
            {
                "title": "🛸 Swarm Integration",
                "description": "Commands for swarm member lifecycle management",
                "color": discord.Color.red(),
                "icon": "🛸",
                "fields": [
                    ("!integrate <agent_id>", "Assimilate new swarm member\nExample: !integrate Agent-1"),
                    ("!onboard <agent_id>", "Initialize swarm member\nExample: !onboard Agent-1"),
                    ("!channels", "View swarm communication network"),
                    ("!status", "Monitor swarm health status")
                ]
            },
            {
                "title": "🖥️ GUI Control",
                "description": "Commands for controlling system GUI through Discord",
                "color": discord.Color.dark_blue(),
                "icon": "🖥️",
                "fields": [
                    ("!gui move <x> <y>", "Move mouse to coordinates\nExample: !gui move 100 200"),
                    ("!gui click", "Click at current position\nExample: !gui click"),
                    ("!gui type <text>", "Type text\nExample: !gui type Hello World"),
                    ("!gui press <key>", "Press a key\nExample: !gui press enter"),
                    ("!gui hotkey <key1> <key2>", "Press key combination\nExample: !gui hotkey ctrl c"),
                    ("!gui screenshot", "Take a screenshot\nExample: !gui screenshot"),
                    ("!gui scroll <amount>", "Scroll mouse wheel\nExample: !gui scroll 10"),
                    ("!gui drag <x> <y>", "Drag mouse to coordinates\nExample: !gui drag 300 400")
                ]
            }
        ]
        
        # Add category buttons with emojis
        self.add_category_buttons()
        
    def add_category_buttons(self):
        """Add category selection buttons with enhanced styling."""
        categories = [
            ("🔄 Core", 0, discord.ButtonStyle.primary),
            ("🎯 Tasks", 1, discord.ButtonStyle.success),
            ("⚡ System", 2, discord.ButtonStyle.danger),
            ("📊 Intelligence", 3, discord.ButtonStyle.secondary),
            ("🛸 Integration", 4, discord.ButtonStyle.primary),
            ("🖥️ GUI", 5, discord.ButtonStyle.success)
        ]
        
        for label, page_num, style in categories:
            button = discord.ui.Button(
                label=label,
                style=style,
                custom_id=f"page_{page_num}",
                row=1,
                emoji=label.split()[0]  # Use the emoji from the label
            )
            button.callback = lambda i, p=page_num: self.jump_to_page(i, p)
            self.add_item(button)
            
    async def jump_to_page(self, interaction: discord.Interaction, page: int):
        """Jump to specific page."""
        self.current_page = page
        await self.update_page(interaction)
        
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to previous page."""
        self.current_page = (self.current_page - 1) % len(self.pages)
        await self.update_page(interaction)
        
    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to next page."""
        self.current_page = (self.current_page + 1) % len(self.pages)
        await self.update_page(interaction)
        
    @discord.ui.button(label="🔍 Search", style=discord.ButtonStyle.success, row=0)
    async def search_commands(self, interaction: discord.Interaction):
        """Open command search modal."""
        modal = CommandSearchModal(self)
        await interaction.response.send_modal(modal)
        
    async def update_page(self, interaction: discord.Interaction):
        """Update the help menu page with enhanced visual design."""
        page = self.pages[self.current_page]
        
        embed = discord.Embed(
            title=f"{page['icon']} {page['title']}",
            description=page["description"],
            color=page["color"]
        )
        
        # Add animated header with custom image
        embed.set_author(
            name="Dream.OS Swarm Command Interface",
            icon_url="https://i.imgur.com/your-swarm-icon.png",
            url="https://github.com/Dadudekc/SWARM"
        )
        
        # Add thumbnail if available
        if "thumbnail" in page:
            embed.set_thumbnail(url=page["thumbnail"])
        
        # Add command fields with enhanced formatting and syntax highlighting
        for name, value in page["fields"]:
            embed.add_field(
                name=f"```ansi\n{name}\n```",
                value=f"```md\n{value}\n```",
                inline=False
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

class DevLogManager:
    """Manages agent development logs and Discord notifications."""
    
    def __init__(self, bot):
        self.bot = bot
        self.log_path = "runtime/agent_memory"
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.channel_id = int(os.getenv('DISCORD_DEVLOG_CHANNEL', 0))
        
    async def update_devlog(self, agent_id: str, message: str, source: str = "manual") -> bool:
        """Update an agent's devlog and notify Discord.
        
        Args:
            agent_id: The ID of the agent
            message: The log message
            source: Source of the update (manual/agent/system)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create agent memory directory if it doesn't exist
            log_path = f"{self.log_path}/{agent_id}/devlog.md"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

            # Format log entry
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
            entry = f"{timestamp} [{source.upper()}] {message}\n"

            # Append to devlog
            with open(log_path, "a") as f:
                f.write(entry)

            # Notify Discord
            await self._notify_discord(agent_id, entry.strip(), source)
            return True

        except Exception as e:
            logger.error(f"Error updating devlog: {e}")
            return False

    async def _notify_discord(self, agent_id: str, message: str, source: str):
        """Send devlog update to Discord."""
        try:
            # Create embed
            embed = discord.Embed(
                title=f"📜 {agent_id} Devlog Update",
                description=message,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Source: {source}")

            # Try webhook first
            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                    await webhook.send(embed=embed)
            # Fallback to channel
            elif self.channel_id:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error notifying Discord: {e}")

    def get_devlog(self, agent_id: str) -> Optional[str]:
        """Get the contents of an agent's devlog."""
        try:
            log_path = f"{self.log_path}/{agent_id}/devlog.md"
            if not os.path.exists(log_path):
                return None

            with open(log_path, 'r') as f:
                return f.read()

        except Exception as e:
            logger.error(f"Error reading devlog: {e}")
            return None

    def clear_devlog(self, agent_id: str) -> bool:
        """Clear an agent's devlog with backup."""
        try:
            log_path = f"{self.log_path}/{agent_id}/devlog.md"
            if not os.path.exists(log_path):
                return False

            # Create backup
            backup_path = f"{log_path}.backup"
            with open(log_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())

            # Clear the log
            with open(log_path, 'w') as f:
                f.write(f"# {agent_id} Devlog\n\n")
                f.write(f"Log cleared at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

            return True

        except Exception as e:
            logger.error(f"Error clearing devlog: {e}")
            return False

class AgentCommands(commands.Cog):
    """Commands for controlling agents via Discord."""
    
    def __init__(self, bot):
        self.bot = bot
        self.processor = MessageProcessor()
        self.devlog = DevLogManager(bot)
        
    async def send_command(self, mode: MessageMode, agent_id: str, content: str) -> bool:
        """Send a command to an agent using the new messaging system."""
        message = Message(
            from_agent="Discord",
            to_agent=agent_id,
            content=content,
            mode=mode
        )
        return self.processor.send_message(message)

    @commands.command(name='swarm_help')
    @commands.cooldown(1, 5)
    async def show_help(self, ctx):
        """Show interactive help menu."""
        menu = HelpMenu()
        page = menu.pages[0]
        
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=discord.Color.blue()
        )
        
        for name, value in page["fields"]:
            embed.add_field(name=name, value=value, inline=False)
            
        embed.set_footer(text=f"Page 1/{len(menu.pages)}")
        await ctx.send(embed=embed, view=menu)
        
    @commands.command(name='list')
    @commands.cooldown(1, 5)
    async def list_agents(self, ctx):
        """List all available agents."""
        agents = sorted(self.bot.agent_resume.coords.keys())
        embed = discord.Embed(
            title="Available Agents",
            description="\n".join(f"• {agent}" for agent in agents),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
    @commands.command(name='resume')
    @commands.cooldown(1, 10)
    async def resume_agent(self, ctx, agent_id: str):
        """Resume an agent's operations."""
        success = await self.send_command(MessageMode.RESUME, agent_id, "Resume operations")
        if success:
            await ctx.send(f"✅ Resumed agent {agent_id}")
        else:
            await ctx.send(f"❌ Failed to resume agent {agent_id}")
            
    @commands.command(name='verify')
    @commands.cooldown(1, 10)
    async def verify_agent(self, ctx, agent_id: str):
        """Verify an agent's integrity."""
        success = await self.send_command(MessageMode.VERIFY, agent_id, "Verify integrity")
        if success:
            await ctx.send(f"✅ Verification request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to verify agent {agent_id}")
            
    @commands.command(name='message')
    @commands.cooldown(1, 5)
    async def send_message(self, ctx, agent_id: str, *, message: str):
        """Send a message to an agent."""
        success = await self.send_command(MessageMode.NORMAL, agent_id, message)
        if success:
            await ctx.send(f"✅ Message sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to send message to {agent_id}")
            
    @commands.command(name='broadcast')
    @commands.cooldown(1, 30)
    async def broadcast_message(self, ctx, *, message: str):
        """Broadcast a message to all agents."""
        success = await self.send_command(MessageMode.BROADCAST, "ALL", message)
        if success:
            await ctx.send("✅ Message broadcasted to all agents")
        else:
            await ctx.send("❌ Failed to broadcast message")
        
    @commands.command(name='agent_status')
    @commands.cooldown(1, 5)
    async def get_status(self, ctx, agent_id: Optional[str] = None):
        """Get status of an agent or all agents."""
        if agent_id:
            success = await self.send_command(MessageMode.STATUS, agent_id, "Get status")
            if success:
                await ctx.send(f"✅ Status request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to get status for {agent_id}")
        else:
            success = await self.send_command(MessageMode.STATUS, "ALL", "Get all status")
            if success:
                await ctx.send("✅ Status request sent to all agents")
            else:
                await ctx.send("❌ Failed to get status for all agents")
        
    @commands.command(name='repair')
    @commands.cooldown(1, 30)
    async def repair_agent(self, ctx, agent_id: str):
        """Repair an agent."""
        success = await self.send_command(MessageMode.REPAIR, agent_id, "Repair agent")
        if success:
            await ctx.send(f"✅ Repair request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to repair agent {agent_id}")
            
    @commands.command(name='backup')
    @commands.cooldown(1, 30)
    async def backup_agent(self, ctx, agent_id: str):
        """Backup an agent's state."""
        success = await self.send_command(MessageMode.BACKUP, agent_id, "Backup state")
        if success:
            await ctx.send(f"✅ Backup request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to backup agent {agent_id}")
            
    @commands.command(name='restore')
    @commands.cooldown(1, 30)
    async def restore_agent(self, ctx, agent_id: str):
        """Restore an agent from backup."""
        success = await self.send_command(MessageMode.RESTORE, agent_id, "Restore from backup")
        if success:
            await ctx.send(f"✅ Restore request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to restore agent {agent_id}")
            
    @commands.command(name='sync')
    @commands.cooldown(1, 30)
    async def sync_agent(self, ctx, agent_id: str):
        """Synchronize an agent."""
        success = await self.send_command(MessageMode.SYNC, agent_id, "Sync agent")
        if success:
            await ctx.send(f"✅ Sync request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to sync agent {agent_id}")
            
    @commands.command(name='cleanup')
    @commands.cooldown(1, 30)
    async def cleanup_agent(self, ctx, agent_id: str):
        """Clean up an agent's resources."""
        success = await self.send_command(MessageMode.CLEANUP, agent_id, "Cleanup resources")
        if success:
            await ctx.send(f"✅ Cleanup request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to cleanup agent {agent_id}")
            
    @commands.command(name='task')
    @commands.cooldown(1, 5)
    async def send_task(self, ctx, agent_ids: str, *, task: str):
        """Send a task to multiple agents."""
        agent_list = [aid.strip() for aid in agent_ids.split(',')]
        success = True
        for agent_id in agent_list:
            if not await self.send_command(MessageMode.TASK, agent_id, task):
                success = False
                break
        if success:
            await ctx.send(f"✅ Task sent to agents: {agent_ids}")
        else:
            await ctx.send(f"❌ Failed to send task to some agents")
        
    @commands.command(name='integrate')
    @commands.cooldown(1, 30)
    async def integrate_agent(self, ctx, agent_id: str):
        """Integrate a new agent."""
        success = await self.send_command(MessageMode.INTEGRATE, agent_id, "Integrate agent")
        if success:
            await ctx.send(f"✅ Integration request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to integrate agent {agent_id}")
            
    @commands.command(name='onboard')
    @commands.cooldown(1, 30)
    async def onboard_agent(self, ctx, agent_id: str):
        """Onboard a new agent."""
        success = await self.send_command(MessageMode.ONBOARD, agent_id, "Onboard agent")
        if success:
            await ctx.send(f"✅ Onboarding request sent to {agent_id}")
        else:
            await ctx.send(f"❌ Failed to onboard agent {agent_id}")
            
    @commands.command(name='multi')
    @commands.cooldown(1, 10)
    async def multi_agent_command(self, ctx, command: str, *, agent_ids: str):
        """Send a command to multiple agents."""
        agent_list = [aid.strip() for aid in agent_ids.split(',')]
        mode = MessageMode[command.upper()]
        success = True
        for agent_id in agent_list:
            if not await self.send_command(mode, agent_id, f"Execute {command}"):
                success = False
                break
        if success:
            await ctx.send(f"✅ {command} command sent to agents: {agent_ids}")
        else:
            await ctx.send(f"❌ Failed to send {command} command to some agents")
        
    @commands.command(name='system')
    @commands.cooldown(1, 30)
    async def system_command(self, ctx, action: str):
        """Execute a system-wide command."""
        mode = MessageMode[action.upper()]
        success = await self.send_command(mode, "ALL", f"Execute system {action}")
        if success:
            await ctx.send(f"✅ System {action} command sent")
        else:
            await ctx.send(f"❌ Failed to execute system {action} command")

    @commands.command(name='gui')
    @commands.cooldown(1, 5)
    async def gui_command(self, ctx, action: str, *, params: str = ""):
        """Execute PyAutoGUI commands through Discord.
        
        Usage: !gui <action> [parameters]
        Actions:
        - move <x> <y>: Move mouse to coordinates
        - click: Click at current position
        - type <text>: Type text
        - press <key>: Press a key
        - hotkey <key1> <key2>: Press key combination
        - screenshot: Take a screenshot
        - scroll <amount>: Scroll mouse wheel
        - drag <x> <y>: Drag mouse to coordinates
        """
        try:
            # Create status embed
            embed = discord.Embed(
                title="🖥️ GUI Command",
                description=f"Executing: {action}",
                color=discord.Color.blue()
            )
            status_msg = await ctx.send(embed=embed)
            
            def execute_gui_command():
                try:
                    if action == "move":
                        x, y = map(int, params.split())
                        pyautogui.moveTo(x, y)
                        return f"Moved mouse to ({x}, {y})"
                        
                    elif action == "click":
                        pyautogui.click()
                        return "Clicked at current position"
                        
                    elif action == "type":
                        pyautogui.write(params)
                        return f"Typed: {params}"
                        
                    elif action == "press":
                        pyautogui.press(params)
                        return f"Pressed key: {params}"
                        
                    elif action == "hotkey":
                        keys = params.split()
                        pyautogui.hotkey(*keys)
                        return f"Pressed hotkey: {' + '.join(keys)}"
                        
                    elif action == "screenshot":
                        screenshot = pyautogui.screenshot()
                        screenshot_path = "runtime/temp/screenshot.png"
                        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                        screenshot.save(screenshot_path)
                        return "Screenshot taken"
                        
                    elif action == "scroll":
                        amount = int(params)
                        pyautogui.scroll(amount)
                        return f"Scrolled {amount} units"
                        
                    elif action == "drag":
                        x, y = map(int, params.split())
                        pyautogui.dragTo(x, y)
                        return f"Dragged to ({x}, {y})"
                        
                    else:
                        return f"Unknown action: {action}"
                        
                except Exception as e:
                    return f"Error: {str(e)}"
            
            # Execute GUI command in a separate thread
            result = await asyncio.get_event_loop().run_in_executor(None, execute_gui_command)
            
            # Update status embed
            embed = discord.Embed(
                title="🖥️ GUI Command Complete",
                description=result,
                color=discord.Color.green()
            )
            
            # If screenshot was taken, attach it
            if action == "screenshot" and "Error" not in result:
                try:
                    await status_msg.edit(embed=embed, file=discord.File("runtime/temp/screenshot.png"))
                except Exception as e:
                    logger.error(f"Error sending screenshot: {e}")
                    await status_msg.edit(embed=embed)
            else:
                await status_msg.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Error executing GUI command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

async def setup(bot):
    """Set up the commands cog."""
    await bot.add_cog(AgentCommands(bot)) 