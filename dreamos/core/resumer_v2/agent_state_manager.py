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
from .atomic_file_manager import AtomicFileManager

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

class AgentStateManager:
    """Manages agent state with event hooks and validation."""
    
    def __init__(self, base_dir: Path):
        """Initialize the agent state manager.
        
        Args:
            base_dir: Base directory for state files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize file managers
        self.state_file = AtomicFileManager(self.base_dir / "agent_state.json")
        self.task_file = AtomicFileManager(self.base_dir / "tasks.json")
        self.debug_log = AtomicFileManager(self.base_dir / "debug_logs/test_debug.log")
        
        # Event system
        self.event_bus = asyncio.Queue()
        self.event_handlers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}
        
        # Initialize state
        self._init_state()
        
    def _init_state(self):
        """Initialize state files with default content."""
        default_state = {
            "cycle_count": 0,
            "last_active": None,
            "mode": "normal",
            "test_debug": {
                "active": False,
                "start_time": None,
                "completed_cycles": 0
            }
        }
        
        default_tasks = {
            "TEST_FIX": [],
            "BLOCKER-TEST-DEBUG": []
        }
        
        # Create tasks but don't await them here
        self._init_state_task = asyncio.create_task(self._initialize_state_files(default_state, default_tasks))
        
    async def _initialize_state_files(self, default_state: Dict[str, Any], default_tasks: Dict[str, List[Dict[str, Any]]]):
        """Initialize state files with default content.
        
        Args:
            default_state: Default state data
            default_tasks: Default tasks data
        """
        await self.state_file.atomic_write(default_state)
        await self.task_file.atomic_write(default_tasks)
        
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
            state: New state data
            
        Returns:
            bool: True if update was successful
        """
        success = await self.state_file.atomic_write(state)
        if success:
            await self._dispatch_event("state_update", state)
        return success
        
    async def add_task(self, task: TaskState) -> bool:
        """Add a new task.
        
        Args:
            task: Task to add
            
        Returns:
            bool: True if task was added successfully
        """
        tasks = await self.task_file.atomic_read()
        if tasks is None:
            tasks = {"TEST_FIX": [], "BLOCKER-TEST-DEBUG": []}
            
        if task.type not in tasks:
            tasks[task.type] = []
            
        tasks[task.type].append({
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "data": task.data
        })
        
        success = await self.task_file.atomic_write(tasks)
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
        tasks = await self.task_file.atomic_read()
        if tasks is None:
            return False
            
        for task_type in tasks:
            for task in tasks[task_type]:
                if task["id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat()
                    if data:
                        task["data"].update(data)
                        
                    success = await self.task_file.atomic_write(tasks)
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
        
        success = await self.debug_log.atomic_write(log_entry)
        if success:
            await self._dispatch_event("debug_log", log_entry)
        return success
        
    async def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current agent state.
        
        Returns:
            Optional[Dict]: Current state or None if unavailable
        """
        return await self.state_file.atomic_read()
        
    async def get_tasks(self, task_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get tasks, optionally filtered by type.
        
        Args:
            task_type: Optional task type to filter by
            
        Returns:
            Optional[Dict]: Tasks or None if unavailable
        """
        tasks = await self.task_file.atomic_read()
        if tasks is None:
            return None
            
        if task_type:
            return {task_type: tasks.get(task_type, [])}
        return tasks
        
    async def validate_state(self) -> bool:
        """Validate current state.
        
        Returns:
            bool: True if state is valid
        """
        state = await self.get_state()
        if state is None:
            return False
            
        required_fields = ["cycle_count", "mode", "test_debug"]
        return all(field in state for field in required_fields)
        
    async def cleanup(self):
        """Clean up resources."""
        await self.state_file.cleanup()
        await self.task_file.cleanup()
        await self.debug_log.cleanup() 