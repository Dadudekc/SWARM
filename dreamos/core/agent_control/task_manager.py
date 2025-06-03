"""
Task Management System

Manages autonomous task distribution and tracking between agents.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('task_manager')

class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"

class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Task:
    """Task data structure."""
    id: str
    title: str
    description: str
    assigned_to: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    dependencies: List[str]
    tags: List[str]
    context: Dict[str, Any]

class TaskManager:
    """Manages task distribution and tracking between agents."""
    
    def __init__(self):
        """Initialize task manager."""
        self.tasks: Dict[str, Task] = {}
        self.task_file = Path("runtime/tasks.json")
        self.task_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_tasks()
        
    def _load_tasks(self) -> None:
        """Load tasks from persistent storage."""
        try:
            if self.task_file.exists():
                with open(self.task_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task(
                            id=task_data['id'],
                            title=task_data['title'],
                            description=task_data['description'],
                            assigned_to=task_data['assigned_to'],
                            status=TaskStatus(task_data['status']),
                            priority=TaskPriority(task_data['priority']),
                            created_at=datetime.fromisoformat(task_data['created_at']),
                            updated_at=datetime.fromisoformat(task_data['updated_at']),
                            dependencies=task_data['dependencies'],
                            tags=task_data['tags'],
                            context=task_data['context']
                        )
                        self.tasks[task.id] = task
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            
    def _save_tasks(self) -> None:
        """Save tasks to persistent storage."""
        try:
            tasks_data = [asdict(task) for task in self.tasks.values()]
            with open(self.task_file, 'w') as f:
                json.dump(tasks_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            
    def create_task(self, title: str, description: str, assigned_to: str,
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   dependencies: List[str] = None,
                   tags: List[str] = None,
                   context: Dict[str, Any] = None) -> Task:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description
            assigned_to: Agent ID to assign task to
            priority: Task priority
            dependencies: List of task IDs this task depends on
            tags: List of tags for the task
            context: Additional context for the task
            
        Returns:
            Created Task object
        """
        task_id = f"task_{len(self.tasks) + 1}"
        now = datetime.now()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            assigned_to=assigned_to,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=now,
            updated_at=now,
            dependencies=dependencies or [],
            tags=tags or [],
            context=context or {}
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Created task {task_id} for {assigned_to}")
        return task
        
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update task status.
        
        Args:
            task_id: ID of task to update
            status: New status
            
        Returns:
            bool: True if update was successful
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
            
        task = self.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now()
        self._save_tasks()
        logger.info(f"Updated task {task_id} status to {status}")
        return True
        
    def get_agent_tasks(self, agent_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get tasks assigned to an agent.
        
        Args:
            agent_id: Agent ID to get tasks for
            status: Optional status filter
            
        Returns:
            List of tasks assigned to agent
        """
        tasks = [task for task in self.tasks.values() if task.assigned_to == agent_id]
        if status:
            tasks = [task for task in tasks if task.status == status]
        return tasks
        
    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks.
        
        Returns:
            List of blocked tasks
        """
        return [task for task in self.tasks.values() if task.status == TaskStatus.BLOCKED]
        
    def get_high_priority_tasks(self) -> List[Task]:
        """Get all high priority tasks.
        
        Returns:
            List of high priority tasks
        """
        return [task for task in self.tasks.values() 
                if task.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL)]
                
    def get_task_context(self) -> Dict[str, Any]:
        """Get context for task management.
        
        Returns:
            Dict containing task management context
        """
        return {
            "total_tasks": len(self.tasks),
            "tasks_by_status": {
                status.value: len([t for t in self.tasks.values() if t.status == status])
                for status in TaskStatus
            },
            "tasks_by_priority": {
                priority.value: len([t for t in self.tasks.values() if t.priority == priority])
                for priority in TaskPriority
            },
            "recent_updates": [
                {
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "updated_at": task.updated_at.isoformat()
                }
                for task in sorted(
                    self.tasks.values(),
                    key=lambda t: t.updated_at,
                    reverse=True
                )[:5]
            ]
        }
        
    def generate_task_summary(self, agent_id: str) -> str:
        """Generate task summary for an agent.
        
        Args:
            agent_id: Agent ID to generate summary for
            
        Returns:
            str: Task summary message
        """
        tasks = self.get_agent_tasks(agent_id)
        if not tasks:
            return f"No tasks currently assigned to {agent_id}"
            
        summary = f"Task Summary for {agent_id}:\n\n"
        
        # Group tasks by status
        tasks_by_status = {}
        for status in TaskStatus:
            status_tasks = [t for t in tasks if t.status == status]
            if status_tasks:
                tasks_by_status[status] = status_tasks
                
        # Add each status group to summary
        for status, status_tasks in tasks_by_status.items():
            summary += f"{status.value.upper()} Tasks:\n"
            for task in status_tasks:
                summary += f"• {task.title} (Priority: {task.priority.name})\n"
            summary += "\n"
            
        return summary 