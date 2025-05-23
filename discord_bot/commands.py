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

from dreamos.core import MessageMode

logger = logging.getLogger('discord_bot')

class HelpMenu(discord.ui.View):
    """Interactive help menu with buttons."""
    
    def __init__(self):
        super().__init__(timeout=180)
        self.current_page = 0
        self.pages = [
            {
                "title": "🔄 Swarm Core Commands",
                "description": "Essential commands for swarm coordination and control",
                "color": discord.Color.purple(),
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
                "fields": [
                    ("!devlog <agent_id> <message>", "Record swarm member development\nExample: !devlog Agent-1 Protocol optimization complete"),
                    ("!clear_devlog <agent_id>", "Reset swarm member development log\nExample: !clear_devlog Agent-1"),
                    ("!devlog_channel", "Configure swarm intelligence channel"),
                    ("!channels", "Display swarm communication channels")
                ]
            },
            {
                "title": "🛸 Swarm Integration",
                "description": "Commands for swarm member lifecycle management",
                "color": discord.Color.red(),
                "fields": [
                    ("!integrate <agent_id>", "Assimilate new swarm member\nExample: !integrate Agent-1"),
                    ("!onboard <agent_id>", "Initialize swarm member\nExample: !onboard Agent-1"),
                    ("!channels", "View swarm communication network"),
                    ("!status", "Monitor swarm health status")
                ]
            }
        ]
        
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to previous page."""
        self.current_page = (self.current_page - 1) % len(self.pages)
        await self.update_page(interaction)
        
    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Navigate to next page."""
        self.current_page = (self.current_page + 1) % len(self.pages)
        await self.update_page(interaction)
        
    async def update_page(self, interaction: discord.Interaction):
        """Update the help menu page with swarm-focused design."""
        page = self.pages[self.current_page]
        
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=page["color"]
        )
        
        # Add swarm-themed header
        embed.set_author(
            name="Dream.OS Swarm Command Interface",
            icon_url="https://i.imgur.com/your-swarm-icon.png"  # Replace with actual icon URL
        )
        
        for name, value in page["fields"]:
            embed.add_field(name=name, value=value, inline=False)
            
        # Add swarm-themed footer
        embed.set_footer(
            text=f"Swarm Intelligence • Page {self.current_page + 1}/{len(self.pages)} • We are the swarm"
        )
        
        await interaction.response.edit_message(embed=embed)

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
    """Commands for controlling agents."""
    
    def __init__(self, bot):
        self.bot = bot
        self.devlog = DevLogManager(bot)
        
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
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            # Send resume message
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.RESUME.value} Initiating autonomous protocol",
                MessageMode.RESUME
            )
            
            if success:
                await ctx.send(f"✅ Successfully resumed {agent_id}")
            else:
                await ctx.send(f"❌ Failed to resume {agent_id}")
                
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")
            
    @commands.command(name='verify')
    @commands.cooldown(1, 10)
    async def verify_agent(self, ctx, agent_id: str):
        """Verify an agent's state."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.VERIFY.value} Please verify your current state",
                MessageMode.VERIFY
            )
            
            if success:
                await ctx.send(f"✅ Verification request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send verification request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error verifying agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")
            
    @commands.command(name='message')
    @commands.cooldown(1, 5)
    async def send_message(self, ctx, agent_id: str, *, message: str):
        """Send a custom message to an agent."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                message,
                MessageMode.NORMAL
            )
            
            if success:
                await ctx.send(f"✅ Message sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send message to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await ctx.send(f"❌ Error: {str(e)}")
            
    @commands.command(name='agent_status')
    @commands.cooldown(1, 5)
    async def get_status(self, ctx, agent_id: Optional[str] = None):
        """Get the status of an agent or all agents."""
        try:
            if agent_id:
                # Get status for specific agent
                status = await self._get_agent_status(agent_id)
                if status:
                    embed = discord.Embed(
                        title=f"🤖 {agent_id} Status",
                        color=discord.Color.blue()
                    )
                    for key, value in status.items():
                        embed.add_field(name=key, value=value, inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ No status found for {agent_id}")
            else:
                # Get status for all agents
                embed = discord.Embed(
                    title="🤖 Swarm Status",
                    color=discord.Color.blue()
                )
                for i in range(1, 9):
                    agent_id = f"Agent-{i}"
                    status = await self._get_agent_status(agent_id)
                    if status:
                        status_text = "\n".join(f"{k}: {v}" for k, v in status.items())
                        embed.add_field(name=agent_id, value=status_text, inline=True)
                await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await ctx.send(f"❌ Error getting status: {str(e)}")
            
    @commands.command(name='broadcast')
    @commands.cooldown(1, 30)
    async def broadcast_message(self, ctx, *, message: str):
        """Send a message to all agents."""
        try:
            self.bot.agent_resume.send_to_all_agents(message)
            await ctx.send("✅ Message broadcast to all agents")
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='prompt')
    @commands.cooldown(1, 5)
    async def send_prompt(self, ctx, agent_id: str, *, prompt_text: str):
        """Send a prompt to an agent's inbox."""
        try:
            # Create agent memory directory if it doesn't exist
            inbox_path = f"runtime/agent_memory/{agent_id}/inbox.json"
            os.makedirs(os.path.dirname(inbox_path), exist_ok=True)

            # Create prompt message
            message = {
                "type": "PROMPT",
                "content": prompt_text,
                "from": str(ctx.author),
                "timestamp": time.time(),
                "channel": str(ctx.channel.id)
            }

            # Write to inbox
            with open(inbox_path, "w") as f:
                json.dump(message, f, indent=2)

            # Send confirmation
            embed = discord.Embed(
                title="🛰️ Prompt Sent",
                description=f"Prompt delivered to `{agent_id}`",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Content",
                value=prompt_text[:1000] + "..." if len(prompt_text) > 1000 else prompt_text,
                inline=False
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='devlog')
    @commands.cooldown(1, 5)
    async def update_devlog(self, ctx, agent_id: str, *, message: str):
        """Update an agent's development log."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return

            success = await self.devlog.update_devlog(agent_id, message, "manual")
            
            if success:
                embed = discord.Embed(
                    title="📜 Devlog Updated",
                    description=f"Devlog updated for `{agent_id}`",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Latest Entry",
                    value=message,
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Failed to update devlog for {agent_id}")

        except Exception as e:
            logger.error(f"Error updating devlog: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='view_devlog')
    @commands.cooldown(1, 5)
    async def view_devlog(self, ctx, agent_id: str):
        """View an agent's development log."""
        try:
            content = self.devlog.get_devlog(agent_id)
            if not content:
                await ctx.send(f"❌ No devlog found for {agent_id}")
                return

            # Split into chunks if too long
            if len(content) > 4000:
                chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
                for i, chunk in enumerate(chunks):
                    embed = discord.Embed(
                        title=f"📜 {agent_id} Devlog (Part {i+1}/{len(chunks)})",
                        description=chunk,
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"📜 {agent_id} Devlog",
                    description=content,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error viewing devlog: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='clear_devlog')
    @commands.cooldown(1, 30)  # Longer cooldown for destructive action
    async def clear_devlog(self, ctx, agent_id: str):
        """Clear an agent's development log."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return

            success = self.devlog.clear_devlog(agent_id)
            
            if success:
                await ctx.send(f"✅ Devlog cleared for {agent_id} (backup created)")
            else:
                await ctx.send(f"❌ Failed to clear devlog for {agent_id}")

        except Exception as e:
            logger.error(f"Error clearing devlog: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='devlog_channel')
    @commands.has_permissions(administrator=True)
    async def set_devlog_channel(self, ctx):
        """Set the current channel as the devlog notification channel."""
        try:
            # Update environment variable
            os.environ['DISCORD_DEVLOG_CHANNEL'] = str(ctx.channel.id)
            
            # Update bot's devlog manager
            self.devlog.channel_id = ctx.channel.id
            
            await ctx.send(f"✅ This channel is now set as the devlog notification channel")
            
        except Exception as e:
            logger.error(f"Error setting devlog channel: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='channels')
    @commands.cooldown(1, 5)
    async def list_channels(self, ctx):
        """List agent channel assignments."""
        try:
            config_path = "runtime/config/agent_channels.yaml"
            if not os.path.exists(config_path):
                await ctx.send("❌ Channel configuration not found")
                return

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            embed = discord.Embed(
                title="Agent Channel Assignments",
                color=discord.Color.blue()
            )

            for agent_id, channel_id in config.items():
                if isinstance(channel_id, str):
                    channel = self.bot.get_channel(int(channel_id))
                    channel_name = channel.name if channel else "Unknown"
                    embed.add_field(
                        name=agent_id,
                        value=f"Channel: {channel_name}\nID: {channel_id}",
                        inline=True
                    )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='repair')
    @commands.cooldown(1, 30)  # Longer cooldown for repair operation
    async def repair_agent(self, ctx, agent_id: str):
        """Repair an agent's state."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.REPAIR.value} Initiating repair protocol",
                MessageMode.REPAIR
            )
            
            if success:
                await ctx.send(f"✅ Repair request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send repair request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error repairing agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='backup')
    @commands.cooldown(1, 30)
    async def backup_agent(self, ctx, agent_id: str):
        """Backup an agent's state."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.BACKUP.value} Initiating backup protocol",
                MessageMode.BACKUP
            )
            
            if success:
                await ctx.send(f"✅ Backup request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send backup request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error backing up agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='restore')
    @commands.cooldown(1, 30)
    async def restore_agent(self, ctx, agent_id: str):
        """Restore an agent's state from backup."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.RESTORE.value} Initiating restore protocol",
                MessageMode.RESTORE
            )
            
            if success:
                await ctx.send(f"✅ Restore request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send restore request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error restoring agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='sync')
    @commands.cooldown(1, 30)
    async def sync_agent(self, ctx, agent_id: str):
        """Synchronize an agent's state with the system."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.SYNC.value} Initiating sync protocol",
                MessageMode.SYNC
            )
            
            if success:
                await ctx.send(f"✅ Sync request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send sync request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error syncing agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='cleanup')
    @commands.cooldown(1, 30)
    async def cleanup_agent(self, ctx, agent_id: str):
        """Clean up an agent's temporary files and cache."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.CLEANUP.value} Initiating cleanup protocol",
                MessageMode.CLEANUP
            )
            
            if success:
                await ctx.send(f"✅ Cleanup request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send cleanup request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='task')
    @commands.cooldown(1, 5)
    async def send_task(self, ctx, agent_ids: str, *, task: str):
        """Send a task to one or more agents."""
        try:
            # Parse agent IDs
            agent_list = [f"Agent-{id.strip()}" for id in agent_ids.split(',')]
            valid_agents = [agent for agent in agent_list if agent in self.bot.agent_resume.coords]
            
            if not valid_agents:
                await ctx.send("❌ No valid swarm members specified")
                return
                
            # Create task embed with swarm theme
            embed = discord.Embed(
                title="🎯 Swarm Task Distribution",
                description=f"**Task Directive:**\n{task}",
                color=discord.Color.blue()
            )
            
            # Add swarm member assignments
            embed.add_field(
                name="🛸 Assigned Swarm Members",
                value="\n".join(f"• {agent}" for agent in valid_agents),
                inline=False
            )
            
            # Add task metadata
            embed.add_field(
                name="📊 Task Metadata",
                value=f"• Priority: Standard\n• Distribution: {len(valid_agents)} members\n• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
            
            status_msg = await ctx.send(embed=embed)
            
            # Process task distribution
            results = []
            for agent_id in valid_agents:
                try:
                    success = self.bot.agent_resume.send_message(
                        agent_id,
                        f"{MessageMode.TASK.value} New swarm directive:\n{task}",
                        MessageMode.TASK
                    )
                    results.append((agent_id, success))
                except Exception as e:
                    results.append((agent_id, False))
                    logger.error(f"Error distributing task to {agent_id}: {e}")
                    
            # Update status with swarm theme
            success_count = sum(1 for _, success in results if success)
            embed = discord.Embed(
                title="🎯 Swarm Task Distribution Complete",
                description=f"**Task Directive:**\n{task}",
                color=discord.Color.green() if success_count == len(valid_agents) else discord.Color.orange()
            )
            
            # Add distribution results
            for agent_id, success in results:
                status = "✅" if success else "❌"
                embed.add_field(
                    name=agent_id,
                    value=f"{status} {'Directive received' if success else 'Distribution failed'}",
                    inline=True
                )
                
            # Add swarm statistics
            embed.add_field(
                name="📊 Swarm Statistics",
                value=f"• Success Rate: {(success_count/len(valid_agents))*100:.1f}%\n• Total Members: {len(valid_agents)}\n• Active Members: {success_count}",
                inline=False
            )
            
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in swarm task distribution: {e}")
            await ctx.send(f"❌ Swarm Error: {str(e)}")

    @commands.command(name='integrate')
    @commands.cooldown(1, 30)
    async def integrate_agent(self, ctx, agent_id: str):
        """Integrate an agent into the system."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.INTEGRATE.value} Initiating integration protocol",
                MessageMode.INTEGRATE
            )
            
            if success:
                await ctx.send(f"✅ Integration request sent to {agent_id}")
            else:
                await ctx.send(f"❌ Failed to send integration request to {agent_id}")
                
        except Exception as e:
            logger.error(f"Error integrating agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='onboard')
    @commands.cooldown(1, 30)
    async def onboard_agent(self, ctx, agent_id: str):
        """Onboard a new agent into the system."""
        try:
            if agent_id not in self.bot.agent_resume.coords:
                await ctx.send(f"❌ Agent {agent_id} not found")
                return
                
            success = self.bot.agent_resume.onboard_single_agent(agent_id)
            
            if success:
                await ctx.send(f"✅ Successfully onboarded {agent_id}")
            else:
                await ctx.send(f"❌ Failed to onboard {agent_id}")
                
        except Exception as e:
            logger.error(f"Error onboarding agent: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name='multi')
    @commands.cooldown(1, 10)
    async def multi_agent_command(self, ctx, command: str, *, agent_ids: str):
        """Execute a command on multiple agents.
        
        Usage: !multi <command> <agent_ids>
        Example: !multi resume 1,3,5
        """
        try:
            # Parse agent IDs
            agent_list = [f"Agent-{id.strip()}" for id in agent_ids.split(',')]
            valid_agents = [agent for agent in agent_list if agent in self.bot.agent_resume.coords]
            
            if not valid_agents:
                await ctx.send("❌ No valid agents specified")
                return
                
            # Map command to function and mode
            command_map = {
                'resume': (MessageMode.RESUME, "Resuming"),
                'verify': (MessageMode.VERIFY, "Verifying"),
                'repair': (MessageMode.REPAIR, "Repairing"),
                'backup': (MessageMode.BACKUP, "Backing up"),
                'restore': (MessageMode.RESTORE, "Restoring"),
                'sync': (MessageMode.SYNC, "Syncing"),
                'cleanup': (MessageMode.CLEANUP, "Cleaning up")
            }
            
            if command not in command_map:
                await ctx.send(f"❌ Invalid command. Available commands: {', '.join(command_map.keys())}")
                return
                
            mode, action = command_map[command]
            
            # Create status embed
            embed = discord.Embed(
                title=f"{action} Multiple Agents",
                description=f"Processing {len(valid_agents)} agents...",
                color=discord.Color.blue()
            )
            status_msg = await ctx.send(embed=embed)
            
            # Process each agent
            results = []
            for agent_id in valid_agents:
                try:
                    success = self.bot.agent_resume.send_message(
                        agent_id,
                        f"{mode.value} Initiating {command} protocol",
                        mode
                    )
                    results.append((agent_id, success))
                except Exception as e:
                    results.append((agent_id, False))
                    logger.error(f"Error processing {agent_id}: {e}")
                    
            # Update status embed
            success_count = sum(1 for _, success in results if success)
            embed = discord.Embed(
                title=f"{action} Complete",
                description=f"Processed {len(valid_agents)} agents",
                color=discord.Color.green() if success_count == len(valid_agents) else discord.Color.orange()
            )
            
            for agent_id, success in results:
                status = "✅" if success else "❌"
                embed.add_field(
                    name=agent_id,
                    value=f"{status} {'Success' if success else 'Failed'}",
                    inline=True
                )
                
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in multi-agent command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

    async def _get_agent_status(self, agent_id: str) -> Dict[str, str]:
        """Get detailed status for an agent."""
        try:
            # Send verify message and wait for response
            success = self.bot.agent_resume.send_message(
                agent_id,
                f"{MessageMode.VERIFY.value} Please report your current status",
                MessageMode.VERIFY
            )
            
            if not success:
                return {"Status": "❌ Unreachable"}
                
            # Wait for response (implement actual response handling)
            await asyncio.sleep(2)  # Placeholder for actual response handling
            
            return {
                "Status": "✅ Active",
                "Last Seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Mode": "Autonomous",
                "Tasks": "0 Pending"
            }
            
        except Exception as e:
            logger.error(f"Error getting status for {agent_id}: {e}")
            return {"Status": f"❌ Error: {str(e)}"}

    @commands.command(name='system')
    @commands.cooldown(1, 30)
    async def system_command(self, ctx, action: str):
        """Execute system-wide operations.
        
        Usage: !system <action>
        Actions: status, sync, backup, cleanup
        """
        try:
            action_map = {
                'status': (MessageMode.VERIFY, "Checking system status"),
                'sync': (MessageMode.SYNC, "Syncing system"),
                'backup': (MessageMode.BACKUP, "Backing up system"),
                'cleanup': (MessageMode.CLEANUP, "Cleaning up system")
            }
            
            if action not in action_map:
                await ctx.send(f"❌ Invalid action. Available actions: {', '.join(action_map.keys())}")
                return
                
            mode, description = action_map[action]
            
            # Create status embed
            embed = discord.Embed(
                title="System Operation",
                description=description,
                color=discord.Color.blue()
            )
            status_msg = await ctx.send(embed=embed)
            
            # Process all agents
            results = []
            for agent_id in self.bot.agent_resume.coords.keys():
                try:
                    success = self.bot.agent_resume.send_message(
                        agent_id,
                        f"{mode.value} Initiating system {action}",
                        mode
                    )
                    results.append((agent_id, success))
                except Exception as e:
                    results.append((agent_id, False))
                    logger.error(f"Error processing {agent_id}: {e}")
                    
            # Update status embed
            success_count = sum(1 for _, success in results if success)
            embed = discord.Embed(
                title=f"System {action.title()} Complete",
                description=f"Processed {len(results)} agents",
                color=discord.Color.green() if success_count == len(results) else discord.Color.orange()
            )
            
            for agent_id, success in results:
                status = "✅" if success else "❌"
                embed.add_field(
                    name=agent_id,
                    value=f"{status} {'Success' if success else 'Failed'}",
                    inline=True
                )
                
            await status_msg.edit(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in system command: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

async def setup(bot):
    """Set up the commands cog."""
    await bot.add_cog(AgentCommands(bot)) 