"""
Discord Bot Commands

Implements commands for controlling agents via Discord.
"""

from tests.utils.mock_discord import commands
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
from dreamos.core.log_manager import LogManager
from social.utils.devlog_manager import DevlogManager
from .log_utils import get_logs_embed

from .help_menu import HelpMenu
logger = logging.getLogger('discord_bot')


class AgentCommands:
    """Commands for managing agents."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_manager = LogManager()
        self.devlog_manager = DevlogManager()
        self.message_processor = MessageProcessor()
        self.cell_phone = CellPhone()
        self.agent_interface = AgentInterface()
        self.command_metrics = CommandMetrics()
        self.config = self._load_config()
        logger.info("Agent commands initialized")
        
        # Register commands
        self.bot.add_command(commands.Command(self.show_help, name="help"))
        self.bot.add_command(commands.Command(self.list_agents, name="list_agents"))
        self.bot.add_command(commands.Command(self.list_channels, name="list_channels"))
        self.bot.add_command(commands.Command(self.send_prompt, name="send_prompt"))
        self.bot.add_command(commands.Command(self.update_devlog, name="update_devlog"))
        self.bot.add_command(commands.Command(self.view_devlog, name="view_devlog"))
        self.bot.add_command(commands.Command(self.clear_devlog, name="clear_devlog"))
        self.bot.add_command(commands.Command(self.resume_agent, name="resume_agent"))
        self.bot.add_command(commands.Command(self.verify_agent, name="verify_agent"))
        self.bot.add_command(commands.Command(self.send_message, name="send_message"))
        self.bot.add_command(commands.Command(self.restore_agent, name="restore_agent"))
        self.bot.add_command(commands.Command(self.sync_agent, name="sync_agent"))
        self.bot.add_command(commands.Command(self.cleanup_agent, name="cleanup_agent"))
        self.bot.add_command(commands.Command(self.multi_command, name="multi_command"))
        self.bot.add_command(commands.Command(self.system_command, name="system_command"))
        self.bot.add_command(commands.Command(self.assign_channel, name="assign_channel"))
        self.bot.add_command(commands.Command(self.show_logs, name="logs"))

    def _load_config(self):
        # Implement the logic to load configuration from the file
        # This is a placeholder and should be replaced with actual implementation
        return {}
    
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
    
    async def show_help(self, ctx):
        """Show the help menu."""
        try:
            menu = HelpMenu()
            await ctx.send(embed=menu.pages[0], view=menu)
        except Exception as e:
            await ctx.send(f"Error showing help menu: {str(e)}")
    
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
    
    async def show_logs(self, ctx, agent_id: str = None, level: str = "info", limit: int = 10):
        """Show logs for an agent or all agents.

        Args:
            agent_id: Optional agent ID to filter logs
            level: Log level (info, warning, error, debug)
            limit: Maximum number of logs to show
        """
        try:
            embed, logs = get_logs_embed(self.log_manager, agent_id, level, limit)

            if not logs:
                await ctx.send(f"No {level} logs found for {agent_id or 'all agents'}")
                return

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