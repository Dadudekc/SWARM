"""Task completion hooks for agent autonomy."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Set

from dreamos.discord.devlog_manager import DiscordDevlog

# Tag categories for better organization
TASK_TAGS = {
    'status': {'done', 'wip', 'blocked', 'failed'},
    'type': {'feature', 'bugfix', 'refactor', 'infra', 'test', 'ops'},
    'priority': {'high', 'medium', 'low'},
    'impact': {'breaking', 'major', 'minor', 'patch'},
    'scope': {'core', 'agent', 'tool', 'test', 'doc'}
}

class TaskCompletionHook:
    """Hook for handling task completion events."""
    
    def __init__(self, agent_id: str, webhook_url: str, footer: str):
        self.agent_id = agent_id
        self.webhook_url = webhook_url
        self.footer = footer
        self.discord_devlog = DiscordDevlog(
            webhook_url=webhook_url,
            agent_name=agent_id,
            footer=footer
        )
        
    def _extract_mentioned_agents(self, content: str) -> Set[str]:
        """Extract mentioned agents from content."""
        import re
        mentions = set()
        for match in re.finditer(r'@Agent-(\d+)', content):
            mentions.add(f"Agent-{match.group(1)}")
        return mentions
        
    def _generate_tags(self, task: Dict) -> List[str]:
        """Generate appropriate tags based on task metadata."""
        tags = []
        
        # Add agent source tag
        tags.append(f"#agent-{self.agent_id.split('-')[1]}")
        
        # Add status tag
        status = task.get('status', 'completed')
        if status in TASK_TAGS['status']:
            tags.append(f"#{status}")
            
        # Add type tag
        task_type = task.get('type', '').lower()
        if task_type in TASK_TAGS['type']:
            tags.append(f"#{task_type}")
            
        # Add priority tag
        priority = task.get('priority', '').lower()
        if priority in TASK_TAGS['priority']:
            tags.append(f"#{priority}")
            
        # Add impact tag
        impact = task.get('impact', '').lower()
        if impact in TASK_TAGS['impact']:
            tags.append(f"#{impact}")
            
        # Add scope tag
        scope = task.get('scope', '').lower()
        if scope in TASK_TAGS['scope']:
            tags.append(f"#{scope}")
            
        # Add mentioned agents as tags
        if task.get('description'):
            mentioned = self._extract_mentioned_agents(task['description'])
            for agent in mentioned:
                tags.append(f"#{agent.lower()}")
                
        return sorted(tags)
        
    def _format_task_summary(self, task: Dict) -> str:
        """Format a task summary for the devlog."""
        summary = []
        
        # Add task title
        summary.append(f"# Task Completed: {task.get('title', 'Untitled Task')}")
        summary.append("")
        
        # Add task details
        if task.get('description'):
            summary.append(f"**Description:** {task['description']}")
            summary.append("")
            
        # Add completion details
        summary.append(f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if task.get('task_id'):
            summary.append(f"**Task ID:** {task['task_id']}")
        summary.append("")
        
        # Add metadata section
        metadata = []
        if task.get('status'):
            metadata.append(f"**Status:** {task['status']}")
        if task.get('type'):
            metadata.append(f"**Type:** {task['type']}")
        if task.get('priority'):
            metadata.append(f"**Priority:** {task['priority']}")
        if task.get('impact'):
            metadata.append(f"**Impact:** {task['impact']}")
        if task.get('scope'):
            metadata.append(f"**Scope:** {task['scope']}")
            
        if metadata:
            summary.extend(metadata)
            summary.append("")
            
        # Add tags
        tags = self._generate_tags(task)
        if tags:
            summary.append(f"**Tags:** {' '.join(tags)}")
            
        return '\n'.join(summary)
        
    async def on_task_complete(self, task: Dict) -> bool:
        """Handle task completion by updating the devlog."""
        try:
            # Format the task summary
            content = self._format_task_summary(task)
            
            # Extract mentioned agents
            mentioned_agents = set()
            if task.get('description'):
                mentioned_agents = self._extract_mentioned_agents(task['description'])
            
            # Update Discord devlog
            success = await self.discord_devlog.update_devlog(
                content=content,
                title=f"Task Completed: {task.get('title', 'Untitled Task')}",
                memory_state={
                    'status': task.get('status', 'completed'),
                    'task_id': task.get('task_id', ''),
                    'type': task.get('type', 'task'),
                    'mentioned_agents': list(mentioned_agents)
                }
            )
            
            if not success:
                print(f"Failed to update devlog for task {task.get('task_id', 'unknown')}")
                return False
                
            # Also update local devlog file
            log_dir = Path(f"dreamos/mailbox/{self.agent_id.lower()}/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            devlog_path = log_dir / "devlog.md"
            with open(devlog_path, 'a', encoding='utf-8') as f:
                f.write('\n\n' + content)
                
            return True
            
        except Exception as e:
            print(f"Error in task completion hook: {e}")
            return False

class TaskCompletionManager:
    """Manage task completion hooks for multiple agents."""
    
    def __init__(self, config_path: str = "dreamos/config/agent_webhooks.json"):
        self.config_path = Path(config_path)
        self.hooks: Dict[str, TaskCompletionHook] = {}
        self._load_config()
        
    def _load_config(self):
        """Load webhook configuration and create hooks."""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
                
            for agent_id, agent_config in config.items():
                self.hooks[agent_id] = TaskCompletionHook(
                    agent_id=agent_id,
                    webhook_url=agent_config['webhook_url'],
                    footer=agent_config['footer']
                )
                
        except Exception as e:
            print(f"Error loading task completion config: {e}")
            
    async def handle_task_completion(self, agent_id: str, task: Dict) -> bool:
        """Handle task completion for a specific agent."""
        if agent_id not in self.hooks:
            print(f"No completion hook found for agent {agent_id}")
            return False
            
        return await self.hooks[agent_id].on_task_complete(task)

# Global instance
task_manager = TaskCompletionManager()

async def on_task_complete(agent_id: str, task: Dict) -> bool:
    """Global task completion handler."""
    return await task_manager.handle_task_completion(agent_id, task) 
