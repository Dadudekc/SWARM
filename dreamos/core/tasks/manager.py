"""
Unified task management system for Dream.OS.

This module provides a centralized task management system that handles
all tasks across the project, including agent tasks, bridge tasks, and system tasks.
"""

import os
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum

class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Priority of a task."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class TaskCategory(Enum):
    """Category of a task."""
    AGENT = "agent"
    BRIDGE = "bridge"
    SYSTEM = "system"
    SOCIAL = "social"
    VALIDATION = "validation"

@dataclass
class Task:
    """Represents a task in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: TaskCategory = TaskCategory.SYSTEM
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None

class TaskManager:
    """Manages tasks across the project."""
    
    def __init__(self, task_root: str = None):
        """Initialize the task manager.
        
        Args:
            task_root: Root directory for task files. If None, uses default.
        """
        self.task_root = task_root or os.path.join(os.path.dirname(__file__), "..", "..", "config", "agent_comms")
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from files."""
        # Load working tasks
        working_tasks_file = os.path.join(self.task_root, "working_tasks.json")
        if os.path.exists(working_tasks_file):
            with open(working_tasks_file, 'r') as f:
                tasks_data = json.load(f)
                for task_data in tasks_data:
                    task = self._dict_to_task(task_data)
                    self.tasks[task.id] = task
        
        # Load future tasks
        future_tasks_file = os.path.join(self.task_root, "future_tasks.json")
        if os.path.exists(future_tasks_file):
            with open(future_tasks_file, 'r') as f:
                tasks_data = json.load(f)
                for task_data in tasks_data:
                    task = self._dict_to_task(task_data)
                    self.tasks[task.id] = task
    
    def _save_tasks(self):
        """Save tasks to files."""
        # Save working tasks
        working_tasks = [
            self._task_to_dict(task)
            for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        ]
        working_tasks_file = os.path.join(self.task_root, "working_tasks.json")
        with open(working_tasks_file, 'w') as f:
            json.dump(working_tasks, f, indent=2, default=str)
        
        # Save future tasks
        future_tasks = [
            self._task_to_dict(task)
            for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
        ]
        future_tasks_file = os.path.join(self.task_root, "future_tasks.json")
        with open(future_tasks_file, 'w') as f:
            json.dump(future_tasks, f, indent=2, default=str)
    
    def _dict_to_task(self, data: Dict[str, Any]) -> Task:
        """Convert a dictionary to a Task object.
        
        Args:
            data: Dictionary containing task data.
            
        Returns:
            Task: Task object.
        """
        return Task(
            id=data.get('id', str(uuid.uuid4())),
            category=TaskCategory(data.get('category', TaskCategory.SYSTEM.value)),
            name=data.get('name', ''),
            description=data.get('description', ''),
            priority=TaskPriority(data.get('priority', TaskPriority.MEDIUM.value)),
            status=TaskStatus(data.get('status', TaskStatus.PENDING.value)),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
            data=data.get('data', {}),
            dependencies=data.get('dependencies', []),
            assigned_to=data.get('assigned_to')
        )
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """Convert a Task object to a dictionary.
        
        Args:
            task: Task object.
            
        Returns:
            Dict[str, Any]: Dictionary containing task data.
        """
        return {
            'id': task.id,
            'category': task.category.value,
            'name': task.name,
            'description': task.description,
            'priority': task.priority.value,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error': task.error,
            'data': task.data,
            'dependencies': task.dependencies,
            'assigned_to': task.assigned_to
        }
    
    def create_task(self, category: TaskCategory, name: str, description: str = "",
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   data: Dict[str, Any] = None,
                   dependencies: List[str] = None) -> Task:
        """Create a new task.
        
        Args:
            category: Task category.
            name: Task name.
            description: Task description.
            priority: Task priority.
            data: Additional task data.
            dependencies: List of task IDs this task depends on.
            
        Returns:
            Task: Created task.
        """
        task = Task(
            category=category,
            name=name,
            description=description,
            priority=priority,
            data=data or {},
            dependencies=dependencies or []
        )
        self.tasks[task.id] = task
        self._save_tasks()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID.
            
        Returns:
            Optional[Task]: Task if found, None otherwise.
        """
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task.
        
        Args:
            task_id: Task ID.
            **kwargs: Fields to update.
            
        Returns:
            Optional[Task]: Updated task if found, None otherwise.
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        self._save_tasks()
        return task
    
    def start_task(self, task_id: str) -> Optional[Task]:
        """Start a task.
        
        Args:
            task_id: Task ID.
            
        Returns:
            Optional[Task]: Started task if found, None otherwise.
        """
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_tasks()
        return task
    
    def complete_task(self, task_id: str, error: Optional[str] = None) -> Optional[Task]:
        """Complete a task.
        
        Args:
            task_id: Task ID.
            error: Error message if task failed.
            
        Returns:
            Optional[Task]: Completed task if found, None otherwise.
        """
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.RUNNING:
            return None
        
        task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.error = error
        self._save_tasks()
        return task
    
    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task.
        
        Args:
            task_id: Task ID.
            
        Returns:
            Optional[Task]: Cancelled task if found, None otherwise.
        """
        task = self.get_task(task_id)
        if not task or task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return None
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        self._save_tasks()
        return task
    
    def get_tasks(self, category: Optional[TaskCategory] = None,
                 status: Optional[TaskStatus] = None,
                 priority: Optional[TaskPriority] = None) -> List[Task]:
        """Get tasks matching criteria.
        
        Args:
            category: Filter by category.
            status: Filter by status.
            priority: Filter by priority.
            
        Returns:
            List[Task]: List of matching tasks.
        """
        tasks = self.tasks.values()
        
        if category:
            tasks = [t for t in tasks if t.category == category]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        
        return sorted(tasks, key=lambda t: t.priority.value, reverse=True)

# Global task manager instance
task_manager = TaskManager()

def create_task(category: TaskCategory, name: str, description: str = "",
               priority: TaskPriority = TaskPriority.MEDIUM,
               data: Dict[str, Any] = None,
               dependencies: List[str] = None) -> Task:
    """Create a new task using the global task manager.
    
    Args:
        category: Task category.
        name: Task name.
        description: Task description.
        priority: Task priority.
        data: Additional task data.
        dependencies: List of task IDs this task depends on.
        
    Returns:
        Task: Created task.
    """
    return task_manager.create_task(category, name, description, priority, data, dependencies)

def get_task(task_id: str) -> Optional[Task]:
    """Get a task by ID using the global task manager.
    
    Args:
        task_id: Task ID.
        
    Returns:
        Optional[Task]: Task if found, None otherwise.
    """
    return task_manager.get_task(task_id)

def update_task(task_id: str, **kwargs) -> Optional[Task]:
    """Update a task using the global task manager.
    
    Args:
        task_id: Task ID.
        **kwargs: Fields to update.
        
    Returns:
        Optional[Task]: Updated task if found, None otherwise.
    """
    return task_manager.update_task(task_id, **kwargs)

def start_task(task_id: str) -> Optional[Task]:
    """Start a task using the global task manager.
    
    Args:
        task_id: Task ID.
        
    Returns:
        Optional[Task]: Started task if found, None otherwise.
    """
    return task_manager.start_task(task_id)

def complete_task(task_id: str, error: Optional[str] = None) -> Optional[Task]:
    """Complete a task using the global task manager.
    
    Args:
        task_id: Task ID.
        error: Error message if task failed.
        
    Returns:
        Optional[Task]: Completed task if found, None otherwise.
    """
    return task_manager.complete_task(task_id, error)

def cancel_task(task_id: str) -> Optional[Task]:
    """Cancel a task using the global task manager.
    
    Args:
        task_id: Task ID.
        
    Returns:
        Optional[Task]: Cancelled task if found, None otherwise.
    """
    return task_manager.cancel_task(task_id)

def get_tasks(category: Optional[TaskCategory] = None,
             status: Optional[TaskStatus] = None,
             priority: Optional[TaskPriority] = None) -> List[Task]:
    """Get tasks matching criteria using the global task manager.
    
    Args:
        category: Filter by category.
        status: Filter by status.
        priority: Filter by priority.
        
    Returns:
        List[Task]: List of matching tasks.
    """
    return task_manager.get_tasks(category, status, priority) 