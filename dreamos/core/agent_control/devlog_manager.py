"""
DevLog Manager

Manages agent development logs and integrates with Discord for real-time updates
and collaboration between agents.
"""

import logging
import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import discord
from discord.ext import commands, tasks
import aiohttp
import yaml

from .task_manager import TaskManager, TaskStatus
from ..cell_phone import CaptainPhone

logger = logging.getLogger('devlog_manager')

class DevLogManager:
    """Manages agent development logs and Discord integration."""

    def __init__(
        self,
        discord_token: Optional[str] = None,
        channel_id: Optional[int] = None,
        webhook_url: Optional[str] = None,
        runtime_dir: Path = Path("runtime"),
    ):
        """Initialize devlog manager.

        Args:
            discord_token: Discord bot token
            channel_id: ID of Discord channel for devlogs
            webhook_url: Optional Discord webhook URL
            runtime_dir: Base runtime directory for logs
        """
        self.discord_token = discord_token or os.getenv("DISCORD_BOT_TOKEN")
        self.channel_id = channel_id or int(os.getenv("DISCORD_DEVLOG_CHANNEL", "0"))
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.runtime_dir = Path(runtime_dir)
        self.log_path = self.runtime_dir / "agent_memory"
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
        self.task_manager = TaskManager()
        self.captain_phone = CaptainPhone()
        
        # Agent devlog channels
        self.agent_channels: Dict[str, int] = {}
        
        # Load configuration
        self.config_path = self.runtime_dir / "config" / "devlog_config.yaml"
        self._load_config()
        
        # Set up Discord bot
        self._setup_bot()
        
    def _load_config(self) -> None:
        """Load devlog configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = {
                    "log_format": "markdown",
                    "update_interval": 300,  # 5 minutes
                    "max_log_length": 2000,
                    "categories": [
                        "development",
                        "research",
                        "collaboration",
                        "system",
                        "tasks"
                    ]
                }
                self._save_config()
        except Exception as e:
            logger.error(f"Error loading devlog config: {e}")
            self.config = {}
            
    def _save_config(self) -> None:
        """Save devlog configuration."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
        except Exception as e:
            logger.error(f"Error saving devlog config: {e}")
            
    def _setup_bot(self) -> None:
        """Set up Discord bot commands and events."""
        
        @self.bot.event
        async def on_ready():
            """Handle bot ready event."""
            logger.info(f"DevLog bot connected as {self.bot.user}")
            self.update_devlogs.start()
            
        @self.bot.command(name="devlog")
        async def devlog(ctx, agent_id: str, category: str, *, content: str):
            """Add a devlog entry for an agent.
            
            Args:
                agent_id: ID of agent
                category: Log category
                content: Log content
            """
            if category not in self.config["categories"]:
                await ctx.send(f"Invalid category. Use one of: {', '.join(self.config['categories'])}")
                return
                
            await self.add_devlog_entry(agent_id, category, content)
            await ctx.send(f"Added devlog entry for {agent_id}")
            
        @self.bot.command(name="summary")
        async def summary(ctx, agent_id: str):
            """Get devlog summary for an agent.
            
            Args:
                agent_id: ID of agent
            """
            summary = await self.generate_agent_summary(agent_id)
            await ctx.send(summary)
            
        @self.bot.command(name="tasks")
        async def tasks(ctx, agent_id: str):
            """Get task summary for an agent.
            
            Args:
                agent_id: ID of agent
            """
            tasks = self.task_manager.get_agent_tasks(agent_id)
            if not tasks:
                await ctx.send(f"No tasks found for {agent_id}")
                return
                
            summary = self.task_manager.generate_task_summary(agent_id)
            await ctx.send(summary)
            
    async def start(self) -> None:
        """Start the devlog manager."""
        try:
            await self.bot.start(self.discord_token)
        except Exception as e:
            logger.error(f"Error starting devlog manager: {e}")
            
    async def stop(self) -> None:
        """Stop the devlog manager."""
        try:
            self.update_devlogs.stop()
            await self.bot.close()
        except Exception as e:
            logger.error(f"Error stopping devlog manager: {e}")
            
    async def add_devlog_entry(self, agent_id: str, category: str, content: str) -> None:
        """Add a devlog entry for an agent.
        
        Args:
            agent_id: ID of agent
            category: Log category
            content: Log content
        """
        try:
            # Format entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "category": category,
                "content": content
            }
            
            # Save to file
            log_file = Path(f"runtime/devlogs/{agent_id}.json")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            entries = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    entries = json.load(f)
                    
            entries.append(entry)
            
            with open(log_file, 'w') as f:
                json.dump(entries, f, indent=2)
                
            # Send to Discord
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"DevLog Entry - {agent_id}",
                    description=content,
                    color=discord.Color.blue()
                )
                embed.add_field(name="Category", value=category)
                embed.add_field(name="Time", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await channel.send(embed=embed)
                
            logger.info(f"Added devlog entry for {agent_id}")

        except Exception as e:
            logger.error(f"Error adding devlog entry: {e}")

    async def add_entry(self, agent_id: str, message: str, source: str = "manual") -> bool:
        """Add a simple log entry and notify Discord.

        Args:
            agent_id: ID of the agent
            message: Log message
            source: Source of the update

        Returns:
            bool: True if the entry was added
        """
        try:
            log_file = self.log_path / agent_id / "devlog.md"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M]")
            entry = f"{timestamp} [{source.upper()}] {message}\n"

            with open(log_file, "a") as f:
                f.write(entry)

            await self._notify_discord(agent_id, entry.strip(), source)
            return True
        except Exception as e:
            logger.error(f"Error updating devlog: {e}")
            return False

    async def _notify_discord(self, agent_id: str, message: str, source: str) -> None:
        """Send a devlog update to Discord."""
        try:
            embed = discord.Embed(
                title=f"📜 {agent_id} Devlog Update",
                description=message,
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Source: {source}")

            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                    await webhook.send(embed=embed)
            elif self.channel_id:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error notifying Discord: {e}")

    async def get_log(self, agent_id: str) -> Optional[str]:
        """Return the contents of an agent's devlog."""
        try:
            log_file = self.log_path / agent_id / "devlog.md"
            if not log_file.exists():
                return None
            return log_file.read_text()
        except Exception as e:
            logger.error(f"Error reading devlog: {e}")
            return None

    async def clear_log(self, agent_id: str) -> bool:
        """Clear an agent devlog with backup."""
        try:
            log_file = self.log_path / agent_id / "devlog.md"
            if not log_file.exists():
                return False

            backup_path = log_file.with_suffix(".md.backup")
            with open(log_file, "r") as src, open(backup_path, "w") as dst:
                dst.write(src.read())

            with open(log_file, "w") as f:
                f.write(f"# {agent_id} Devlog\n\n")
                f.write(f"Log cleared at {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

            return True
        except Exception as e:
            logger.error(f"Error clearing devlog: {e}")
            return False
            
    async def generate_agent_summary(self, agent_id: str) -> str:
        """Generate summary of agent's devlog entries.
        
        Args:
            agent_id: ID of agent
            
        Returns:
            str: Summary of devlog entries
        """
        try:
            log_file = Path(f"runtime/devlogs/{agent_id}.json")
            if not log_file.exists():
                return f"No devlog entries found for {agent_id}"
                
            with open(log_file, 'r') as f:
                entries = json.load(f)
                
            # Group entries by category
            entries_by_category = {}
            for entry in entries:
                category = entry["category"]
                if category not in entries_by_category:
                    entries_by_category[category] = []
                entries_by_category[category].append(entry)
                
            # Generate summary
            summary = f"DevLog Summary for {agent_id}\n\n"
            
            for category, category_entries in entries_by_category.items():
                summary += f"## {category.upper()}\n"
                for entry in category_entries[-5:]:  # Show last 5 entries per category
                    timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                    summary += f"• [{timestamp}] {entry['content'][:100]}...\n"
                summary += "\n"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating agent summary: {e}")
            return f"Error generating summary for {agent_id}: {str(e)}"
            
    @tasks.loop(minutes=5)
    async def update_devlogs(self) -> None:
        """Periodic task to update devlogs."""
        try:
            # Get all agent devlogs
            devlog_dir = Path("runtime/devlogs")
            if not devlog_dir.exists():
                return
                
            for log_file in devlog_dir.glob("*.json"):
                agent_id = log_file.stem
                
                # Generate summary
                summary = await self.generate_agent_summary(agent_id)
                
                # Get task summary
                task_summary = self.task_manager.generate_task_summary(agent_id)
                
                # Send update to Discord
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    embed = discord.Embed(
                        title=f"Agent Update - {agent_id}",
                        description="Periodic update of agent activity",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="DevLog Summary", value=summary[:1000] + "...")
                    embed.add_field(name="Task Summary", value=task_summary[:1000] + "...")
                    await channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Error updating devlogs: {e}")
            
    async def notify_agent_activity(self, agent_id: str, activity_type: str, details: str) -> None:
        """Notify about agent activity.
        
        Args:
            agent_id: ID of agent
            activity_type: Type of activity
            details: Activity details
        """
        try:
            # Add to devlog
            await self.add_devlog_entry(agent_id, "system", f"{activity_type}: {details}")
            
            # Notify other agents
            self.captain_phone.send_message(
                to_agent="all",
                content=f"Agent {agent_id} {activity_type}: {details}",
                mode="BROADCAST",
                priority=2
            )
            
        except Exception as e:
            logger.error(f"Error notifying agent activity: {e}")
            
    def get_agent_devlog(self, agent_id: str, category: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get devlog entries for an agent.
        
        Args:
            agent_id: ID of agent
            category: Optional category filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            List of devlog entries
        """
        try:
            log_file = Path(f"runtime/devlogs/{agent_id}.json")
            if not log_file.exists():
                return []
                
            with open(log_file, 'r') as f:
                entries = json.load(f)
                
            # Apply filters
            filtered_entries = []
            for entry in entries:
                # Category filter
                if category and entry["category"] != category:
                    continue
                    
                # Time filters
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if start_time and entry_time < start_time:
                    continue
                if end_time and entry_time > end_time:
                    continue
                    
                filtered_entries.append(entry)
                
            return filtered_entries
            
        except Exception as e:
            logger.error(f"Error getting agent devlog: {e}")
            return [] 