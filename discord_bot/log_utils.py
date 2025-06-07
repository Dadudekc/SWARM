"""Utility functions for Discord bot logging."""

from typing import Optional, Tuple, List
import discord

from dreamos.core.log_manager import LogManager


def get_logs_embed(log_manager: LogManager, agent_id: Optional[str], level: str, limit: int) -> Tuple[discord.Embed, List[dict]]:
    """Return an embed and log entries for the given parameters."""
    logs = log_manager.read_logs(
        platform=agent_id or "all",
        level=level.upper(),
        limit=limit,
    )

    embed = discord.Embed(
        title=f"Logs for {agent_id or 'All Agents'}",
        description=f"Showing {len(logs)} {level} logs",
        color=discord.Color.blue(),
    )

    for log in logs:
        timestamp = log.get("timestamp", "Unknown")
        message = log.get("message", "No message")
        status = log.get("status", "Unknown")
        embed.add_field(name=f"{timestamp} - {status}", value=message, inline=False)

    return embed, logs
