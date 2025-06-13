import logging
from typing import Optional, Dict, Any, List

from ..messaging.unified_message_system import MessageSystem, MessageMode, MessagePriority
from ..messaging.common import Message
from ..messaging.enums import TaskPriority, TaskStatus
from .task_manager import TaskManager


class Captain:
    """Central coordinator for agents.

    The Captain assigns tasks and routes messages using the
    :class:`MessageSystem`. It also keeps track of tasks via
    :class:`TaskManager`.
    """

    def __init__(self, ums: Optional[MessageSystem] = None, task_manager: Optional[TaskManager] = None):
        self.ums = ums or MessageSystem()
        self.task_manager = task_manager or TaskManager()
        self.logger = logging.getLogger("dreamos.captain")

    async def assign_task(
        self,
        agent_id: str,
        name: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Create a task for ``agent_id`` and notify them.

        Returns the created task id or ``None`` on failure.
        """
        try:
            task = self.task_manager.create_task(
                name=name,
                description=description,
                agent_id=agent_id,
                priority=priority,
                metadata=metadata or {},
            )

            await self.ums.send(
                to_agent=agent_id,
                content=description,
                mode=MessageMode.TASK,
                priority=MessagePriority(min(priority.value, len(MessagePriority) - 1)),
                from_agent="captain",
                metadata={"task_id": task.task_id},
            )
            return task.task_id
        except Exception as exc:  # pragma: no cover - log unexpected errors
            self.logger.error("Failed to assign task to %s: %s", agent_id, exc)
            return None

    async def prioritize_tasks(self) -> List[Dict[str, Any]]:
        """Return all tasks sorted by priority (highest first)."""
        try:
            tasks = sorted(
                self.task_manager._tasks.values(),
                key=lambda t: t.priority.value,
                reverse=True,
            )
            return [t.to_dict() for t in tasks]
        except Exception as exc:  # pragma: no cover - log unexpected errors
            self.logger.error("Failed to gather tasks: %s", exc)
            return []

    async def handle_message(self, message: Message) -> None:
        """Process a message directed to the captain."""
        try:
            if message.content.startswith("task_complete:"):
                _, task_id = message.content.split(":", 1)
                self.task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        except Exception as exc:  # pragma: no cover - log unexpected errors
            self.logger.error(
                "Error processing response from %s: %s", message.from_agent, exc
            )


