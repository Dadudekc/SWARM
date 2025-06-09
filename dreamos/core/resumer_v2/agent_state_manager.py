"""
Agent State Manager

Manages agent state with event hooks and validation.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Awaitable
import logging
import json
import aiofiles
import uuid
from dreamos.core.messaging.enums import TaskStatus

logger = logging.getLogger(__name__)

@dataclass
class TaskState:
    """Represents a task in the system."""
    id: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime
    data: Dict[str, Any]

class TaskStatusEncoder(json.JSONEncoder):
    """Custom JSON encoder for TaskStatus enum."""
    def default(self, obj):
        if isinstance(obj, TaskStatus):
            return obj.value
        return super().default(obj)

class AgentStateManager:
    """Manages agent state with event hooks and validation."""
    
    def __init__(self, base_dir: str):
        """Initialize the state manager.
        
        Args:
            base_dir: Base directory for state files
        """
        self.base_dir = Path(base_dir)
        self.state_file = self.base_dir / "state.json"
        self.tasks_file = self.base_dir / "tasks.json"
        self.debug_log = self.base_dir / "debug.log"
        
        # Initialize state files if they don't exist
        self._init_state()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}
        
    def _init_state(self):
        """Initialize state files with default values."""
        if not self.state_file.exists():
            self._write_state_file({
                "cycle_count": 0,
                "debug_mode": False,
                "last_updated": datetime.now().isoformat()
            })
        
        if not self.tasks_file.exists():
            self._write_tasks_file({})
            
        # Load current state
        self._load_state()
        self._load_tasks()
        
    async def register_event_handler(self, event_type: str, handler: Callable[[Any], Awaitable[None]]):
        """Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    async def _dispatch_event(self, event_type: str, data: Any):
        """Dispatch an event to registered handlers.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Event handler failed: {str(e)}")
                    
    async def update_state(self, state: Dict[str, Any]) -> bool:
        """Update agent state.
        
        Args:
            state: New state dictionary
            
        Returns:
            bool: True if update was successful
        """
        success = await self._write_state_file_async(state)
        if success:
            await self._dispatch_event("state_updated", state)
        return success
        
    async def add_task(self, task: Dict[str, Any]) -> bool:
        """Add a new task.
        
        Args:
            task: Task dictionary
            
        Returns:
            bool: True if task was added successfully
        """
        tasks = await self._load_tasks_async()
        if tasks is None:
            tasks = {}
            
        task_type = task["type"]
        if task_type not in tasks:
            tasks[task_type] = []
            
        tasks[task_type].append({
            "id": task["id"],
            "type": task["type"],
            "status": task["status"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
            "data": task["data"]
        })
        
        success = await self._write_tasks_file_async(tasks)
        if success:
            await self._dispatch_event("task_added", task)
        return success
        
    async def update_task(self, task_id: str, status: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing task.
        
        Args:
            task_id: ID of task to update
            status: New status
            data: Optional additional data
            
        Returns:
            bool: True if update was successful
        """
        tasks = await self._load_tasks_async()
        if tasks is None:
            return False
            
        for task_type in tasks:
            for task in tasks[task_type]:
                if task["id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat()
                    if data:
                        task["data"].update(data)
                        
                    success = await self._write_tasks_file_async(tasks)
                    if success:
                        await self._dispatch_event("task_updated", task)
                    return success
                    
        return False
        
    async def log_debug(self, message: str) -> bool:
        """Log a debug message.
        
        Args:
            message: Message to log
            
        Returns:
            bool: True if logging was successful
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        try:
            async with aiofiles.open(self.debug_log, 'a') as f:
                await f.write(json.dumps(log_entry) + "\n")
            return True
        except Exception as e:
            logger.error(f"Error writing debug log: {e}")
            return False
            
    async def cleanup(self):
        """Clean up resources."""
        if self.state_file.exists():
            self.state_file.unlink()
        if self.tasks_file.exists():
            self.tasks_file.unlink()
        if self.debug_log.exists():
            self.debug_log.unlink()
            
    def _write_state_file(self, state: Dict[str, Any]) -> bool:
        """Write state to file synchronously.
        
        Args:
            state: State dictionary to write
            
        Returns:
            bool: True if write was successful
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing state file: {e}")
            return False
            
    def _write_tasks_file(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Write tasks to file synchronously.
        
        Args:
            tasks: Tasks dictionary to write
            
        Returns:
            bool: True if write was successful
        """
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks, f, indent=2, cls=TaskStatusEncoder)
            return True
        except Exception as e:
            logger.error(f"Error writing tasks file: {e}")
            return False
            
    async def _write_state_file_async(self, state: Dict[str, Any]) -> bool:
        """Write state to file asynchronously.
        
        Args:
            state: State dictionary to write
            
        Returns:
            bool: True if write was successful
        """
        try:
            async with aiofiles.open(self.state_file, 'w') as f:
                await f.write(json.dumps(state, indent=2))
            return True
        except Exception as e:
            logger.error(f"Error writing state file: {e}")
            return False
            
    async def _write_tasks_file_async(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Write tasks to file asynchronously.
        
        Args:
            tasks: Tasks dictionary to write
            
        Returns:
            bool: True if write was successful
        """
        try:
            async with aiofiles.open(self.tasks_file, 'w') as f:
                await f.write(json.dumps(tasks, indent=2, cls=TaskStatusEncoder))
            return True
        except Exception as e:
            logger.error(f"Error writing tasks file: {e}")
            return False
            
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file synchronously.
        
        Returns:
            Dict[str, Any]: Current state or empty dict if file doesn't exist
        """
        try:
            if not self.state_file.exists():
                return {}
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state file: {e}")
            return {}
            
    def _load_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load tasks from file synchronously.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Current tasks or empty dict if file doesn't exist
        """
        try:
            if not self.tasks_file.exists():
                return {}
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks file: {e}")
            return {}
            
    async def _load_state_async(self) -> Dict[str, Any]:
        """Load state from file asynchronously.
        
        Returns:
            Dict[str, Any]: Current state or empty dict if file doesn't exist
        """
        try:
            if not self.state_file.exists():
                return {}
            async with aiofiles.open(self.state_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading state file: {e}")
            return {}
            
    async def _load_tasks_async(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load tasks from file asynchronously.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Current tasks or empty dict if file doesn't exist
        """
        try:
            if not self.tasks_file.exists():
                return {}
            async with aiofiles.open(self.tasks_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error loading tasks file: {e}")
            return {}
            
    async def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return await self._load_state_async()

    async def get_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current tasks."""
        return await self._load_tasks_async()

    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate state structure."""
        required_fields = {"cycle_count", "debug_mode", "last_updated"}
        return all(field in state for field in required_fields)

    def validate_tasks(self, tasks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Validate tasks structure."""
        if not isinstance(tasks, dict):
            return False
        for task_list in tasks.values():
            if not isinstance(task_list, list):
                return False
            for task in task_list:
                if not isinstance(task, dict):
                    return False
                if "status" not in task:
                    return False
        return True 
