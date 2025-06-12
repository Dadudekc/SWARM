"""Message builder module for creating consistent UI messages.

This module provides a centralized system for creating and managing UI messages
across the application. It uses a template-based approach to ensure consistency
in message formatting and content.

The MessageBuilder class is implemented as a singleton to maintain a single source
of truth for message templates and formatting rules.

Example:
    ```python
    from dreamos.core.messaging.message_builder import message_builder, MessageType
    
    # Create a success message
    message = message_builder.create_message(
        MessageType.SUCCESS,
        "task_complete",
        {"task_name": "Backup"}
    )
    
    # Create an error message
    message = message_builder.create_message(
        MessageType.ERROR,
        "task_failed",
        {"error": "Permission denied"}
    )
    ```
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dreamos.core.messaging.message import Message, MessageMode

class MessageType(Enum):
    """Enumeration of message types.
    
    Attributes:
        SUCCESS: Indicates successful operation completion
        ERROR: Indicates operation failure
        INFO: General information message
        WARNING: Warning message
        PROGRESS: Progress update message
        STATUS: Status update message
        COMMAND: Command-related message
        SYSTEM: System-level message
    """
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"
    PROGRESS = "progress"
    STATUS = "status"
    COMMAND = "command"
    SYSTEM = "system"

@dataclass
class MessageTemplate:
    """Template for creating messages.
    
    Attributes:
        type: The type of message (SUCCESS, ERROR, etc.)
        template: The template string with placeholders
        mode: The message mode (TASK, SYSTEM, etc.)
        default_data: Default values for template placeholders
    """
    type: MessageType
    template: str
    mode: MessageMode
    default_data: Dict[str, Any]

class MessageBuilder:
    """Builder for creating consistent UI messages.
    
    This class implements the singleton pattern to ensure a single source of truth
    for message templates and formatting rules across the application.
    
    Attributes:
        _templates: Dictionary of message templates by type and name
    """
    
    def __init__(self):
        """Initialize the message builder with default templates."""
        self._templates: Dict[MessageType, Dict[str, MessageTemplate]] = {
            MessageType.SUCCESS: {
                "task_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Task completed: {task_name}",
                    MessageMode.TASK,
                    {"task_name": "Unknown task"}
                ),
                "backup_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Backup completed successfully at {backup_path}",
                    MessageMode.TASK,
                    {"backup_path": "unknown location"}
                ),
                "sync_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Synchronization completed successfully",
                    MessageMode.TASK,
                    {}
                ),
                "verify_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Verification completed successfully",
                    MessageMode.TASK,
                    {}
                ),
                "repair_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Repair completed successfully",
                    MessageMode.TASK,
                    {}
                ),
                "cleanup_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Cleanup completed successfully",
                    MessageMode.TASK,
                    {}
                ),
                "integrate_complete": MessageTemplate(
                    MessageType.SUCCESS,
                    "✅ Integration completed successfully",
                    MessageMode.TASK,
                    {}
                )
            },
            MessageType.ERROR: {
                "task_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Task failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "sync_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Synchronization failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "verify_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Verification failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "repair_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Repair failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "backup_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Backup failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "restore_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Restore failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "cleanup_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Cleanup failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                ),
                "integrate_failed": MessageTemplate(
                    MessageType.ERROR,
                    "❌ Integration failed: {error}",
                    MessageMode.TASK,
                    {"error": "Unknown error"}
                )
            },
            MessageType.INFO: {
                "task_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting task: {task_name}",
                    MessageMode.TASK,
                    {"task_name": "Unknown task"}
                ),
                "sync_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting synchronization",
                    MessageMode.TASK,
                    {}
                ),
                "verify_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting verification",
                    MessageMode.TASK,
                    {}
                ),
                "repair_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting repair",
                    MessageMode.TASK,
                    {}
                ),
                "backup_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting backup",
                    MessageMode.TASK,
                    {}
                ),
                "restore_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting restore",
                    MessageMode.TASK,
                    {}
                ),
                "cleanup_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting cleanup",
                    MessageMode.TASK,
                    {}
                ),
                "integrate_started": MessageTemplate(
                    MessageType.INFO,
                    "ℹ️ Starting integration of {component}",
                    MessageMode.TASK,
                    {"component": "Unknown component"}
                )
            },
            MessageType.PROGRESS: {
                "task_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Task progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "sync_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Synchronization progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "verify_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Verification progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "repair_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Repair progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "backup_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Backup progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "restore_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Restore progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "cleanup_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Cleanup progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                ),
                "integrate_progress": MessageTemplate(
                    MessageType.PROGRESS,
                    "⏳ Integration progress: {progress}%",
                    MessageMode.TASK,
                    {"progress": 0}
                )
            }
        }
    
    def create_message(
        self,
        msg_type: MessageType,
        template_name: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Message:
        """Create a new message using the specified template.
        
        Args:
            msg_type: The type of message to create
            template_name: Name of the template to use
            data: Dictionary of data to format the template with
            **kwargs: Additional properties to set on the message
            
        Returns:
            Message: The created message
            
        Raises:
            KeyError: If the template type or name is not found
        """
        if msg_type not in self._templates:
            raise KeyError(f"Unknown message type: {msg_type}")
            
        if template_name not in self._templates[msg_type]:
            raise KeyError(f"Unknown template: {template_name}")
            
        template = self._templates[msg_type][template_name]
        
        # Merge default data with provided data
        message_data = template.default_data.copy()
        if data:
            message_data.update(data)
            
        # Format the template string
        content = template.template.format(**message_data)
        
        # Create and return the message
        return Message(
            content=content,
            type=template.mode,
            data=message_data,
            **kwargs
        )
    
    def add_template(
        self,
        msg_type: MessageType,
        template_name: str,
        template: str,
        mode: MessageMode,
        default_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new message template.
        
        Args:
            msg_type: The type of message
            template_name: Name for the template
            template: The template string with placeholders
            mode: The message mode
            default_data: Default values for template placeholders
        """
        if msg_type not in self._templates:
            self._templates[msg_type] = {}
            
        self._templates[msg_type][template_name] = MessageTemplate(
            msg_type,
            template,
            mode,
            default_data or {}
        )
    
    def remove_template(self, msg_type: MessageType, template_name: str) -> None:
        """Remove a message template.
        
        Args:
            msg_type: The type of message
            template_name: Name of the template to remove
            
        Raises:
            KeyError: If the template type or name is not found
        """
        if msg_type not in self._templates:
            raise KeyError(f"Unknown message type: {msg_type}")
            
        if template_name not in self._templates[msg_type]:
            raise KeyError(f"Unknown template: {template_name}")
            
        del self._templates[msg_type][template_name]

# Create singleton instance
message_builder = MessageBuilder() 