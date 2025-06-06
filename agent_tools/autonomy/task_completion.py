"""Task completion hooks for agent autonomy."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..swarm_tools.discord_devlog import DiscordDevlog

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
        
        # Add status and tags
        status = task.get('status', 'completed')
        summary.append(f"**Status:** {status}")
        
        # Add relevant tags
        tags = []
        if status == 'completed':
            tags.append('#done')
        if task.get('priority') == 'high':
            tags.append('#priority')
        if task.get('type') == 'bug':
            tags.append('#bugfix')
        if task.get('type') == 'feature':
            tags.append('#feature')
            
        if tags:
            summary.append(f"**Tags:** {' '.join(tags)}")
            
        return '\n'.join(summary)
        
    async def on_task_complete(self, task: Dict) -> bool:
        """Handle task completion by updating the devlog."""
        try:
            # Format the task summary
            content = self._format_task_summary(task)
            
            # Update Discord devlog
            success = await self.discord_devlog.update_devlog(
                content=content,
                title=f"Task Completed: {task.get('title', 'Untitled Task')}",
                memory_state={
                    'status': task.get('status', 'completed'),
                    'task_id': task.get('task_id', ''),
                    'type': task.get('type', 'task')
                }
            )
            
            if not success:
                print(f"Failed to update devlog for task {task.get('task_id', 'unknown')}")
                return False
                
            # Also update local devlog file
            log_dir = Path(f"agent_tools/mailbox/{self.agent_id.lower()}/logs")
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
    
    def __init__(self, config_path: str = "agent_tools/swarm_tools/agent_webhooks.json"):
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