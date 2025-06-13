"""
Task Management System

Manages autonomous task distribution and tracking between agents.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from enum import Enum
from uuid import uuid4
from dreamos.core.messaging.enums import TaskStatus, TaskPriority

logger = logging.getLogger('task_manager')

@dataclass
class Task:
    """Task structure for agent operations."""
    name: str
    description: str
    agent_id: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "status": self.status.name,
            "priority": self.priority.name,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "task_id": self.task_id,
            "metadata": self.metadata,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            agent_id=data["agent_id"],
            status=TaskStatus[data.get("status", "PENDING")],
            priority=TaskPriority[data.get("priority", "NORMAL")],
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            task_id=data["task_id"],
            metadata=data.get("metadata", {}),
            result=data.get("result"),
            error=data.get("error")
        )
    
    def validate(self) -> bool:
        """Validate task fields."""
        if not self.name or not self.description or not self.agent_id:
            return False
        if not isinstance(self.status, TaskStatus):
            return False
        if not isinstance(self.priority, TaskPriority):
            return False
        return True

class TaskManager:
    """Manages task distribution and tracking between agents."""
    
    def __init__(self):
        """Initialize task manager."""
        self._tasks: Dict[str, Task] = {}
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
                            name=task_data['name'],
                            description=task_data['description'],
                            agent_id=task_data['agent_id'],
                            status=TaskStatus(task_data['status']),
                            priority=TaskPriority(task_data['priority']),
                            created_at=datetime.fromisoformat(task_data['created_at']),
                            started_at=datetime.fromisoformat(task_data['started_at']) if task_data.get('started_at') else None,
                            completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None,
                            task_id=task_data['task_id'],
                            metadata=task_data['metadata'],
                            result=task_data.get('result'),
                            error=task_data.get('error')
                        )
                        self._tasks[task.task_id] = task
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            
    def _save_tasks(self) -> None:
        """Save tasks to persistent storage."""
        try:
            tasks_data = [task.to_dict() for task in self._tasks.values()]
            with open(self.task_file, 'w') as f:
                json.dump(tasks_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            
    def create_task(
        self,
        name: str,
        description: str,
        agent_id: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            name=name,
            description=description,
            agent_id=agent_id,
            priority=priority,
            metadata=metadata or {}
        )
        self._tasks[task.task_id] = task
        self._save_tasks()
        logger.info(f"Created task {task.task_id} for {agent_id}")
        return task
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)
        
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update task status and result."""
        task = self._tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        task.status = status
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = datetime.now()
            task.result = result
            task.error = error
        
        self._save_tasks()
        logger.info(f"Updated task {task_id} status to {status}")
        return True
        
    def get_agent_tasks(
        self,
        agent_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Get all tasks for an agent."""
        tasks = [task for task in self._tasks.values() if task.agent_id == agent_id]
        if status:
            tasks = [task for task in tasks if task.status == status]
        return tasks
        
    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks.
        
        Returns:
            List of blocked tasks
        """
        return [task for task in self._tasks.values() if task.status == TaskStatus.BLOCKED]
        
    def get_high_priority_tasks(self) -> List[Task]:
        """Get all high priority tasks.
        
        Returns:
            List of high priority tasks
        """
        return [task for task in self._tasks.values() 
                if task.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL)]
                
    def get_task_context(self) -> Dict[str, Any]:
        """Get context for task management.
        
        Returns:
            Dict containing task management context
        """
        return {
            "total_tasks": len(self._tasks),
            "tasks_by_status": {
                status.name: len([t for t in self._tasks.values() if t.status == status])
                for status in TaskStatus
            },
            "tasks_by_priority": {
                priority.name: len([t for t in self._tasks.values() if t.priority == priority])
                for priority in TaskPriority
            },
            "recent_updates": [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status.name,
                    "updated_at": task.completed_at.isoformat() if task.completed_at else task.created_at.isoformat()
                }
                for task in sorted(
                    self._tasks.values(),
                    key=lambda t: t.completed_at or t.created_at,
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
            summary += f"{status.name.upper()} Tasks:\n"
            for task in status_tasks:
                summary += f"• {task.name} (Priority: {task.priority.name})\n"
            summary += "\n"
            
        return summary

    def cleanup_completed_tasks(self, max_age_days: int = 7) -> int:
        """Remove old completed tasks."""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                if task.completed_at:
                    age = (now - task.completed_at).days
                    if age > max_age_days:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
        
        self._save_tasks()
        return len(to_remove) 
