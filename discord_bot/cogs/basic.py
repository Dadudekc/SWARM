"""Basic command set for the Dream.OS Discord bot using a Cog."""

from discord.ext import commands
from social.utils.log_manager import LogManager


class BasicCommands(commands.Cog):
    """Group core bot commands into a Cog for easier management."""

    def __init__(self, orchestrator, log_manager: LogManager):
        self.orchestrator = orchestrator
        self.log_manager = log_manager

    @commands.command(name="help")
    async def cmd_help(self, ctx: commands.Context) -> None:
        """Show help information."""
        help_text = (
            "**Dream.OS Bot Commands**\n\n"
            "`!help` - Show this help message\n"
            "`!status <agent_id>` - Show agent status\n"
            "`!task <agent_id> <title> <description>` - Create new task\n"
            "`!devlog <agent_id> <category> <content>` - Add devlog entry"
        )
        await ctx.send(help_text)
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Help command executed by {ctx.author}",
            tags=["command", "help"],
        )

    @commands.command(name="status")
    async def cmd_status(self, ctx: commands.Context, agent_id: str) -> None:
        """Show agent status."""
        status = await self.orchestrator.get_agent_status(agent_id)
        msg = f"**Status for Agent {agent_id}**\n\n"
        msg += "**Tasks**\n"
        msg += f"Total: {status['tasks']['total']}\n"
        msg += f"Summary: {status['tasks']['summary']}\n\n"
        msg += "**DevLog**\n"
        msg += f"Total Entries: {status['devlog']['total_entries']}\n\n"
        msg += "**Messages**\n"
        msg += f"Total: {status['messages']['total']}\n"
        await ctx.send(msg)
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Status command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "status"],
        )

    @commands.command(name="task")
    async def cmd_task(
        self, ctx: commands.Context, agent_id: str, title: str, *, description: str
    ) -> None:
        """Create a new task for an agent."""
        task_id = await self.orchestrator.create_agent_task(
            agent_id=agent_id, title=title, description=description
        )
        await ctx.send(f"Task created with ID: {task_id}")
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Task command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "task"],
        )

    @commands.command(name="devlog")
    async def cmd_devlog(
        self, ctx: commands.Context, agent_id: str, category: str, *, content: str
    ) -> None:
        """Add a devlog entry for an agent."""
        await self.orchestrator.devlog_manager.add_devlog_entry(
            agent_id=agent_id,
            category=category,
            content=content,
            author=str(ctx.author),
        )
        await ctx.send("Devlog entry added successfully")
        self.log_manager.info(
            platform="commands",
            status="success",
            message=f"Devlog command executed for agent {agent_id} by {ctx.author}",
            tags=["command", "devlog"],
        )

