"""
Message-related enums for Dream.OS.
Consolidates all messaging-related enumerations in one place.
"""

from enum import Enum, auto

class MessageMode(Enum):
    """Modes for message delivery."""
    NORMAL = auto()  # Default mode
    TASK = auto()    # Task-related message
    SYSTEM = auto()  # System message
    SYNC = auto()    # Synchronization message
    VERIFY = auto()  # Verification message
    REPAIR = auto()  # Repair message
    BACKUP = auto()  # Backup message
    RESTORE = auto() # Restore message
    CLEANUP = auto() # Cleanup message
    CAPTAIN = auto() # Captain message
    INTEGRATE = auto() # Integration message

class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class MessageType(Enum):
    """Types of messages in the system."""
    SUCCESS = "success"  # Success message
    ERROR = "error"      # Error message
    INFO = "info"        # Information message
    WARNING = "warning"  # Warning message
    PROGRESS = "progress" # Progress update
    STATUS = "status"    # Status update
    COMMAND = "command"  # Command message
    SYSTEM = "system"    # System message

class MessageStatus(Enum):
    """Message delivery and processing status."""
    PENDING = auto()     # Message is queued
    SENT = auto()        # Message has been sent
    DELIVERED = auto()   # Message has been delivered
    READ = auto()        # Message has been read
    PROCESSING = auto()  # Message is being processed
    COMPLETED = auto()   # Message processing completed
    FAILED = auto()      # Message processing failed
    CANCELLED = auto()   # Message was cancelled
    TIMEOUT = auto()     # Message processing timed out
    BLOCKED = auto()     # Message is blocked
    RETRYING = auto()    # Message is being retried
    DISCARDED = auto()   # Message was discarded

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = auto()     # Task is queued
    RUNNING = auto()     # Task is executing
    COMPLETED = auto()   # Task finished successfully
    FAILED = auto()      # Task encountered an error
    CANCELLED = auto()   # Task was cancelled
    TIMEOUT = auto()     # Task exceeded time limit
    BLOCKED = auto()     # Task is waiting for resources

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    MEDIUM = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5 
