"""Devlog-specific Discord commands."""

from tests.utils.mock_discord import commands
import logging
import discord
import io
from social.utils.devlog_manager import DevlogManager

logger = logging.getLogger('discord_bot')


class DevlogCommands:
    """Commands for managing agent development logs."""

    def __init__(self, bot: commands.Bot, devlog_manager: DevlogManager | None = None):
        self.bot = bot
        self.devlog_manager = devlog_manager or DevlogManager()

        # register commands
        self.bot.add_command(commands.Command(self.update_devlog, name="update_devlog"))
        self.bot.add_command(commands.Command(self.view_devlog, name="view_devlog"))
        self.bot.add_command(commands.Command(self.clear_devlog, name="clear_devlog"))

    async def update_devlog(self, ctx, agent_id: str, message: str):
        """Append a message to an agent's devlog."""
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
        except Exception as e:  # pragma: no cover - log unexpected errors
            logger.error("update_devlog failed: %s", e, exc_info=True)
            await ctx.send(f"Failed to update devlog: {str(e)}")

    async def view_devlog(self, ctx, agent_id: str):
        """Retrieve an agent's devlog and send it as a file."""
        try:
            devlog_content = await self.devlog_manager.get_log(agent_id)
            if not devlog_content:
                await ctx.send(f"No devlog found for agent {agent_id}.")
                return
            filename = f"{agent_id}_devlog.md"
            file = discord.File(io.StringIO(devlog_content), filename=filename)
            await ctx.send(f"Devlog for agent {agent_id}:", file=file)
        except Exception as e:  # pragma: no cover - log unexpected errors
            logger.error("view_devlog failed for %s: %s", agent_id, e, exc_info=True)
            await ctx.send(f"Error viewing devlog for agent {agent_id}: {str(e)}")

    async def clear_devlog(self, ctx, agent_id: str):
        """Clear an agent's devlog."""
        try:
            if not agent_id:
                await ctx.send("Agent ID is required.")
                return
            success = await self.devlog_manager.clear_log(agent_id)
            if success:
                await ctx.send("Devlog cleared")
            else:
                await ctx.send("Failed to clear devlog")
        except Exception as e:  # pragma: no cover - log unexpected errors
            logger.error("clear_devlog failed: %s", e, exc_info=True)
            await ctx.send(f"Failed to clear devlog: {str(e)}")
