"""
Task Scheduler
-------------
Handles task prioritization and execution scheduling for the Captain.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from queue import PriorityQueue

from .captain import Task, TaskPriority

logger = logging.getLogger("dreamos.captain.scheduler")

@dataclass
class ScheduledTask:
    """Represents a task scheduled for execution."""
    task: Task
    scheduled_time: datetime
    priority_score: float

class TaskScheduler:
    """Manages task scheduling and prioritization."""
    
    def __init__(self):
        """Initialize the task scheduler."""
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue = PriorityQueue()
        self.running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start the task scheduler."""
        if not self.running:
            self.running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the task scheduler."""
        if self.running:
            self.running = False
            if self._scheduler_task:
                self._scheduler_task.cancel()
            logger.info("Task scheduler stopped")
    
    def _calculate_priority_score(self, task: Task) -> float:
        """Calculate priority score for a task.
        
        Args:
            task: The task to score
            
        Returns:
            float: Priority score (higher = more urgent)
        """
        base_score = {
            TaskPriority.CRITICAL: 100.0,
            TaskPriority.HIGH: 75.0,
            TaskPriority.NORMAL: 50.0,
            TaskPriority.LOW: 25.0
        }[task.priority]
        
        # Adjust for deadline
        if task.deadline:
            time_until_deadline = (task.deadline - datetime.now()).total_seconds()
            if time_until_deadline < 0:
                # Overdue task gets highest priority
                return 200.0
            elif time_until_deadline < 3600:  # Less than 1 hour
                base_score *= 1.5
            elif time_until_deadline < 86400:  # Less than 1 day
                base_score *= 1.2
        
        # Adjust for dependencies
        if task.dependencies:
            base_score *= 1.1  # Tasks with dependencies get slight priority boost
        
        return base_score
    
    async def schedule_task(self, task: Task) -> bool:
        """Schedule a task for execution.
        
        Args:
            task: The task to schedule
            
        Returns:
            bool: True if task was scheduled successfully
        """
        try:
            # Calculate priority score
            priority_score = self._calculate_priority_score(task)
            
            # Create scheduled task
            scheduled_task = ScheduledTask(
                task=task,
                scheduled_time=datetime.now(),
                priority_score=priority_score
            )
            
            # Add to scheduled tasks
            self.scheduled_tasks[task.task_id] = scheduled_task
            
            # Add to priority queue
            self.task_queue.put((-priority_score, task.task_id))
            
            logger.info(f"Scheduled task {task.task_id} with priority score {priority_score}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule task {task.task_id}: {e}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            bool: True if task was cancelled successfully
        """
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            logger.info(f"Cancelled task {task_id}")
            return True
        return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                # Get next task from queue
                if not self.task_queue.empty():
                    _, task_id = self.task_queue.get()
                    if task_id in self.scheduled_tasks:
                        scheduled_task = self.scheduled_tasks[task_id]
                        
                        # Check if task is ready to execute
                        if self._is_task_ready(scheduled_task.task):
                            # Execute task
                            await self._execute_task(scheduled_task.task)
                            
                            # Remove from scheduled tasks
                            del self.scheduled_tasks[task_id]
                
                # Sleep briefly to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(1)  # Back off on error
    
    def _is_task_ready(self, task: Task) -> bool:
        """Check if a task is ready to execute.
        
        Args:
            task: The task to check
            
        Returns:
            bool: True if task is ready to execute
        """
        # Check dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                if dep_id in self.scheduled_tasks:
                    return False
        
        # Check deadline
        if task.deadline and datetime.now() > task.deadline:
            return True  # Overdue tasks are always ready
        
        return True
    
    async def _execute_task(self, task: Task):
        """Execute a task.
        
        Args:
            task: The task to execute
        """
        try:
            # Here we would trigger the actual task execution
            # This would typically involve sending a message to the assigned agent
            logger.info(f"Executing task {task.task_id}")
            
            # Task execution logic would go here
            # For now, we just log the execution
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
    
    def get_scheduled_tasks(self, agent_id: Optional[str] = None) -> List[ScheduledTask]:
        """Get list of scheduled tasks.
        
        Args:
            agent_id: Optional agent ID to filter tasks
            
        Returns:
            List[ScheduledTask]: List of scheduled tasks
        """
        if agent_id:
            return [
                scheduled_task
                for scheduled_task in self.scheduled_tasks.values()
                if scheduled_task.task.agent_id == agent_id
            ]
        return list(self.scheduled_tasks.values()) 