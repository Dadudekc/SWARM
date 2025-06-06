"""Weekly digest generator for swarm activity."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional

import aiohttp
import click
from rich.console import Console
from rich.panel import Panel

from agent_tools.swarm_tools.discord_devlog import DiscordDevlog

class DevlogEntry:
    """Represents a single devlog entry with metadata."""
    
    def __init__(self, content: str, timestamp: datetime, agent_id: str):
        """Initialize a devlog entry.
        
        Args:
            content: The full content of the devlog entry
            timestamp: When the entry was created
            agent_id: Which agent created the entry
        """
        self.content = content
        self.timestamp = timestamp
        self.agent_id = agent_id
        self.tags: Set[str] = set()
        self.mentioned_agents: Set[str] = set()
        self._parse_content()
    
    def _parse_content(self):
        """Extract tags and mentioned agents from content."""
        # Extract hashtags
        self.tags = set(re.findall(r'#(\w+)', self.content))
        
        # Extract agent mentions
        self.mentioned_agents = set(re.findall(r'@Agent-\d+', self.content))

class WeeklyDigest:
    """Generates weekly summaries of swarm activity."""
    
    def __init__(self, webhook_url: str):
        """Initialize the weekly digest generator.
        
        Args:
            webhook_url: Discord webhook URL for posting digests
        """
        self.webhook_url = webhook_url
        self.console = Console()
        self.discord_devlog = DiscordDevlog(webhook_url)
    
    def _load_agent_logs(self, start_date: datetime, end_date: datetime) -> List[DevlogEntry]:
        """Load and parse devlog entries from all agents.
        
        Args:
            start_date: Start of the period to analyze
            end_date: End of the period to analyze
            
        Returns:
            List of parsed devlog entries
        """
        entries = []
        mailbox_dir = Path(__file__).resolve().parent.parent / "mailbox"
        
        # Load webhook config for agent info
        config_path = Path(__file__).resolve().parent / "webhook_config.json"
        with open(config_path) as f:
            agent_configs = json.load(f)
        
        # Process each agent's logs
        for agent_id, config in agent_configs.items():
            agent_dir = mailbox_dir / agent_id.lower() / "logs"
            if not agent_dir.exists():
                continue
                
            devlog_path = agent_dir / "devlog.md"
            if not devlog_path.exists():
                continue
                
            with open(devlog_path) as f:
                content = f.read()
                
            # Split into individual entries
            entry_texts = content.split("---")
            for entry_text in entry_texts:
                if not entry_text.strip():
                    continue
                    
                # Extract timestamp
                timestamp_match = re.search(r'\*\*Completed:\*\* ([\d-]+ [\d:]+)', entry_text)
                if not timestamp_match:
                    continue
                    
                try:
                    timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                    if start_date <= timestamp <= end_date:
                        entries.append(DevlogEntry(entry_text, timestamp, agent_id))
                except ValueError:
                    continue
        
        return sorted(entries, key=lambda e: e.timestamp)
    
    def _generate_agent_stats(self, entries: List[DevlogEntry]) -> Dict:
        """Generate statistics for each agent.
        
        Args:
            entries: List of devlog entries to analyze
            
        Returns:
            Dictionary of agent statistics
        """
        stats = {}
        
        for entry in entries:
            if entry.agent_id not in stats:
                stats[entry.agent_id] = {
                    "total_entries": 0,
                    "tags": set(),
                    "mentioned_by": set(),
                    "mentioned_others": set(),
                    "last_active": entry.timestamp
                }
            
            agent_stats = stats[entry.agent_id]
            agent_stats["total_entries"] += 1
            agent_stats["tags"].update(entry.tags)
            agent_stats["mentioned_others"].update(entry.mentioned_agents)
            agent_stats["last_active"] = max(agent_stats["last_active"], entry.timestamp)
            
            # Update mentioned_by for other agents
            for mentioned in entry.mentioned_agents:
                if mentioned not in stats:
                    stats[mentioned] = {
                        "total_entries": 0,
                        "tags": set(),
                        "mentioned_by": set(),
                        "mentioned_others": set(),
                        "last_active": entry.timestamp
                    }
                stats[mentioned]["mentioned_by"].add(entry.agent_id)
        
        return stats
    
    def _format_digest(self, entries: List[DevlogEntry], stats: Dict) -> str:
        """Format the weekly digest content.
        
        Args:
            entries: List of devlog entries
            stats: Dictionary of agent statistics
            
        Returns:
            Formatted digest content
        """
        content = ["# Weekly Swarm Activity Digest\n"]
        
        # Agent summaries
        content.append("## Agent Activity Summary")
        for agent_id, agent_stats in sorted(stats.items()):
            content.append(f"\n### {agent_id}")
            content.append(f"Total entries: {agent_stats['total_entries']}")
            
            if agent_stats["tags"]:
                content.append(f"Tags used: {', '.join(sorted(agent_stats['tags']))}")
            
            if agent_stats["mentioned_by"]:
                content.append(f"Mentioned by: {', '.join(sorted(agent_stats['mentioned_by']))}")
            
            if agent_stats["mentioned_others"]:
                content.append(f"Mentioned others: {', '.join(sorted(agent_stats['mentioned_others']))}")
            
            content.append(f"Last active: {agent_stats['last_active'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Recent activity
        content.append("\n## Recent Activity")
        for entry in entries[-5:]:  # Show last 5 entries
            content.append(f"\n### {entry.agent_id} - {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            content.append(entry.content.strip())
        
        return "\n".join(content)
    
    async def generate_digest(self, days: int = 7) -> bool:
        """Generate and post the weekly digest.
        
        Args:
            days: Number of days to include in the digest
            
        Returns:
            True if successful, False otherwise
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Load and analyze entries
            entries = self._load_agent_logs(start_date, end_date)
            if not entries:
                self.console.print("[yellow]No entries found in the specified period")
                return False
            
            stats = self._generate_agent_stats(entries)
            content = self._format_digest(entries, stats)
            
            # Post to Discord
            memory_state = {
                "period_days": days,
                "total_entries": len(entries),
                "active_agents": len(stats),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            success = await self.discord_devlog.update_devlog(
                title=f"Weekly Swarm Digest ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})",
                content=content,
                memory_state=memory_state
            )
            
            if success:
                self.console.print("[green]Weekly digest posted successfully")
            else:
                self.console.print("[red]Failed to post weekly digest")
            
            return success
            
        except Exception as e:
            self.console.print(f"[red]Error generating digest: {str(e)}")
            return False

@click.command()
@click.option("--webhook-url", required=True, help="Discord webhook URL")
@click.option("--days", default=7, help="Number of days to include in digest")
def main(webhook_url: str, days: int):
    """Generate and post a weekly digest of swarm activity."""
    digest = WeeklyDigest(webhook_url)
    
    console = Console()
    with console.status("[bold blue]Generating weekly digest..."):
        success = asyncio.run(digest.generate_digest(days))
    
    if not success:
        console.print("[red]Failed to generate digest")
        sys.exit(1)

if __name__ == "__main__":
    main() 