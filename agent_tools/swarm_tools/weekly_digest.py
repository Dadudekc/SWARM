"""Weekly digest generator for swarm activity."""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

import aiohttp
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import sys

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
        config_path = Path(__file__).resolve().parent / "agent_webhooks.json"
        if config_path.exists():
            with open(config_path) as f:
                agent_configs = json.load(f)
        else:
            # Fallback: use agent directories in mailbox
            agent_configs = {p.name.capitalize(): {} for p in mailbox_dir.iterdir() if p.is_dir()}
        
        # Process each agent's logs
        for agent_id, config in agent_configs.items():
            agent_dir = mailbox_dir / agent_id.lower() / "logs"
            if not agent_dir.exists():
                continue
            
            # Look for both devlog.md and date-based devlog files
            devlog_files = list(agent_dir.glob("devlog*.md"))
            if not devlog_files:
                continue
            
            for devlog_path in devlog_files:
                # Try to extract date from filename
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', devlog_path.name)
                if date_match:
                    try:
                        file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                        if not (start_date <= file_date <= end_date):
                            continue
                    except ValueError:
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
                        # If no timestamp in content, use file date
                        if date_match:
                            timestamp = file_date
                        else:
                            continue
                    else:
                        try:
                            timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            continue
                    
                    if start_date <= timestamp <= end_date:
                        entries.append(DevlogEntry(entry_text, timestamp, agent_id))
        
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
                    "last_active": entry.timestamp,
                    "first_entry": entry.timestamp,
                    "wip_tasks": set(),
                    "completed_tasks": set()
                }
            
            agent_stats = stats[entry.agent_id]
            agent_stats["total_entries"] += 1
            agent_stats["tags"].update(entry.tags)
            agent_stats["mentioned_others"].update(entry.mentioned_agents)
            agent_stats["last_active"] = max(agent_stats["last_active"], entry.timestamp)
            agent_stats["first_entry"] = min(agent_stats["first_entry"], entry.timestamp)
            
            # Track task status
            if "wip" in entry.tags:
                agent_stats["wip_tasks"].add(entry.content.split("\n")[0])
            if "done" in entry.tags:
                agent_stats["completed_tasks"].add(entry.content.split("\n")[0])
            
            # Update mentioned_by for other agents
            for mentioned in entry.mentioned_agents:
                if mentioned not in stats:
                    stats[mentioned] = {
                        "total_entries": 0,
                        "tags": set(),
                        "mentioned_by": set(),
                        "mentioned_others": set(),
                        "last_active": entry.timestamp,
                        "first_entry": entry.timestamp,
                        "wip_tasks": set(),
                        "completed_tasks": set()
                    }
                stats[mentioned]["mentioned_by"].add(entry.agent_id)
        
        return stats
    
    def _generate_insights(self, entries: List[DevlogEntry], stats: Dict) -> Dict:
        """Generate strategic insights from the data.
        
        Args:
            entries: List of devlog entries
            stats: Dictionary of agent statistics
            
        Returns:
            Dictionary of insights
        """
        insights = {
            "top_contributors": [],
            "silent_agents": [],
            "longest_wip": [],
            "most_mentioned": [],
            "tag_usage": {},
            "collaboration_pairs": []
        }
        
        # Top contributors by entry count
        sorted_agents = sorted(
            stats.items(),
            key=lambda x: x[1]["total_entries"],
            reverse=True
        )
        insights["top_contributors"] = [
            (agent_id, data["total_entries"])
            for agent_id, data in sorted_agents[:3]
        ]
        
        # Silent agents (no entries in period)
        insights["silent_agents"] = [
            agent_id for agent_id, data in stats.items()
            if data["total_entries"] == 0
        ]
        
        # Longest WIP tasks
        wip_tasks = []
        for agent_id, data in stats.items():
            for task in data["wip_tasks"]:
                wip_tasks.append((agent_id, task))
        insights["longest_wip"] = wip_tasks[:3]  # Top 3 longest WIP
        
        # Most mentioned agents
        mentioned_counts = {
            agent_id: len(data["mentioned_by"])
            for agent_id, data in stats.items()
        }
        insights["most_mentioned"] = sorted(
            mentioned_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Tag usage
        tag_counts = {}
        for data in stats.values():
            for tag in data["tags"]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        insights["tag_usage"] = dict(sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        # Collaboration pairs
        for agent_id, data in stats.items():
            for mentioned in data["mentioned_others"]:
                if mentioned in stats:  # Only count if mentioned agent exists
                    insights["collaboration_pairs"].append((agent_id, mentioned))
        
        return insights
    
    def _format_insights(self, insights: Dict) -> str:
        """Format the insights section of the digest.
        
        Args:
            insights: Dictionary of insights
            
        Returns:
            Formatted insights content
        """
        content = ["## Strategic Insights\n"]
        
        # Top contributors
        content.append("### Top Contributors")
        for agent_id, count in insights["top_contributors"]:
            content.append(f"- {agent_id}: {count} entries")
        
        # Silent agents
        if insights["silent_agents"]:
            content.append("\n### Silent Agents")
            for agent_id in insights["silent_agents"]:
                content.append(f"- {agent_id}")
        
        # Longest WIP
        if insights["longest_wip"]:
            content.append("\n### Longest WIP Tasks")
            for agent_id, task in insights["longest_wip"]:
                content.append(f"- {agent_id}: {task}")
        
        # Most mentioned
        content.append("\n### Most Mentioned Agents")
        for agent_id, count in insights["most_mentioned"]:
            content.append(f"- {agent_id}: mentioned {count} times")
        
        # Tag usage
        content.append("\n### Tag Usage")
        for tag, count in list(insights["tag_usage"].items())[:5]:  # Top 5 tags
            content.append(f"- #{tag}: {count} uses")
        
        # Collaboration pairs
        if insights["collaboration_pairs"]:
            content.append("\n### Active Collaborations")
            for agent1, agent2 in insights["collaboration_pairs"]:
                content.append(f"- {agent1} ↔️ {agent2}")
        
        return "\n".join(content)
    
    def _format_digest(self, entries: List[DevlogEntry], stats: Dict) -> str:
        """Format the weekly digest content.
        
        Args:
            entries: List of devlog entries
            stats: Dictionary of agent statistics
            
        Returns:
            Formatted digest content
        """
        content = ["# Weekly Swarm Activity Digest\n"]
        
        # Generate and add insights
        insights = self._generate_insights(entries, stats)
        content.append(self._format_insights(insights))
        
        # Agent summaries
        content.append("\n## Agent Activity Summary")
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
            
            if agent_stats["wip_tasks"]:
                content.append(f"\nWIP Tasks:")
                for task in agent_stats["wip_tasks"]:
                    content.append(f"- {task}")
            
            if agent_stats["completed_tasks"]:
                content.append(f"\nCompleted Tasks:")
                for task in agent_stats["completed_tasks"]:
                    content.append(f"- {task}")
        
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