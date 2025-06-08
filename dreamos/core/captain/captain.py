"""
Captain Module
-------------
Provides centralized oversight and coordination of agent activities.
Handles task prioritization, agent state management, and system monitoring.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum, auto
from queue import PriorityQueue
import uuid

from ..messaging.unified_message_system import UnifiedMessageSystem
from ..messaging.common import Message, MessageMode, MessagePriority

logger = logging.getLogger("dreamos.captain")

class TaskPriority(Enum):
    """Priority levels for tasks."""
    CRITICAL = auto()
    HIGH = auto()
    NORMAL = auto()
    LOW = auto()

@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    task_id: str
    agent_id: str
    description: str
    priority: TaskPriority
    created_at: datetime
    deadline: Optional[datetime] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    status: str = "pending"

class Captain:
    """Oversees agent coordination and task management."""
    
    def __init__(self, message_system: UnifiedMessageSystem):
        """Initialize the Captain.
        
        Args:
            message_system: The unified message system for communication
        """
        self.message_system = message_system
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, Task] = {}
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Task] = []
        
        # Subscribe to system messages
        asyncio.create_task(self._setup_subscriptions())
    
    async def _setup_subscriptions(self):
        """Set up message subscriptions for system monitoring."""
        await self.message_system.subscribe(
            "system",
            self._handle_system_message
        )
        await self.message_system.subscribe_pattern(
            "agent.*",
            self._handle_agent_message
        )
    
    async def _handle_system_message(self, message: Message):
        """Handle system-level messages.
        
        Args:
            message: The received message
        """
        if message.mode == MessageMode.SYSTEM:
            # Handle system events like agent registration, errors, etc.
            if "event" in message.metadata:
                await self._process_system_event(message.metadata["event"], message)
    
    async def _handle_agent_message(self, message: Message):
        """Handle agent messages for state tracking.
        
        Args:
            message: The received message
        """
        agent_id = message.from_agent
        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = {}
        
        # Update agent state based on message
        if "state" in message.metadata:
            self.agent_states[agent_id].update(message.metadata["state"])
    
    async def _process_system_event(self, event: str, message: Message):
        """Process system events.
        
        Args:
            event: The event type
            message: The event message
        """
        if event == "agent_registered":
            await self._handle_agent_registration(message)
        elif event == "agent_error":
            await self._handle_agent_error(message)
        elif event == "task_completed":
            await self._handle_task_completion(message)
    
    async def _handle_agent_registration(self, message: Message):
        """Handle new agent registration.
        
        Args:
            message: The registration message
        """
        agent_id = message.metadata.get("agent_id")
        if agent_id:
            self.agent_states[agent_id] = {
                "status": "active",
                "registered_at": datetime.now(),
                "capabilities": message.metadata.get("capabilities", [])
            }
            logger.info(f"Agent {agent_id} registered with Captain")
    
    async def _handle_agent_error(self, message: Message):
        """Handle agent error reports.
        
        Args:
            message: The error message
        """
        agent_id = message.from_agent
        if agent_id in self.agent_states:
            self.agent_states[agent_id]["last_error"] = {
                "timestamp": datetime.now(),
                "error": message.content,
                "details": message.metadata.get("error_details", {})
            }
            logger.error(f"Agent {agent_id} reported error: {message.content}")
    
    async def _handle_task_completion(self, message: Message):
        """Handle task completion notifications.
        
        Args:
            message: The completion message
        """
        task_id = message.metadata.get("task_id")
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            task.status = "completed"
            self.task_history.append(task)
            logger.info(f"Task {task_id} completed by {message.from_agent}")
    
    async def assign_task(
        self,
        agent_id: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assign a new task to an agent.
        
        Args:
            agent_id: The agent to assign the task to
            description: Task description
            priority: Task priority
            deadline: Optional task deadline
            dependencies: Optional list of task dependencies
            metadata: Optional task metadata
            
        Returns:
            str: The assigned task ID
        """
        task = Task(
            task_id=f"task_{len(self.task_history) + 1}",
            agent_id=agent_id,
            description=description,
            priority=priority,
            created_at=datetime.now(),
            deadline=deadline,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        # Check dependencies
        if dependencies:
            for dep_id in dependencies:
                if dep_id in self.active_tasks:
                    logger.warning(f"Task {task.task_id} depends on incomplete task {dep_id}")
                    return None
        
        # Add to active tasks
        self.active_tasks[task.task_id] = task
        
        # Send task assignment message
        await self.message_system.send(
            to_agent=agent_id,
            content=description,
            mode=MessageMode.COMMAND,
            priority=MessagePriority.HIGH if priority in [TaskPriority.CRITICAL, TaskPriority.HIGH] else MessagePriority.NORMAL,
            from_agent="captain",
            metadata={
                "task_id": task.task_id,
                "priority": priority.name,
                "deadline": deadline.isoformat() if deadline else None,
                "dependencies": dependencies,
                **(metadata or {})
            }
        )
        
        logger.info(f"Assigned task {task.task_id} to {agent_id}")
        return task.task_id
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an agent.
        
        Args:
            agent_id: The agent ID to check
            
        Returns:
            Optional[Dict[str, Any]]: Agent status information
        """
        return self.agent_states.get(agent_id)
    
    async def get_active_tasks(self, agent_id: Optional[str] = None) -> List[Task]:
        """Get list of active tasks.
        
        Args:
            agent_id: Optional agent ID to filter tasks
            
        Returns:
            List[Task]: List of active tasks
        """
        if agent_id:
            return [task for task in self.active_tasks.values() if task.agent_id == agent_id]
        return list(self.active_tasks.values())
    
    async def get_task_history(self, agent_id: Optional[str] = None) -> List[Task]:
        """Get task history.
        
        Args:
            agent_id: Optional agent ID to filter history
            
        Returns:
            List[Task]: List of completed tasks
        """
        if agent_id:
            return [task for task in self.task_history if task.agent_id == agent_id]
        return self.task_history

    def create_task(self, description: str, priority: TaskPriority = TaskPriority.NORMAL, metadata: Optional[Dict] = None) -> Task:
        """Create a new task.
        
        Args:
            description: Task description
            priority: Task priority
            metadata: Optional task metadata
            
        Returns:
            Task: Created task
        """
        task = Task(
            task_id=str(uuid.uuid4()),
            agent_id="",
            description=description,
            priority=priority,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        self.active_tasks[task.task_id] = task
        return task 
