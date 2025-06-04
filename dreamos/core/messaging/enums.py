"""
Message-related enums for Dream.OS.
Consolidates all messaging-related enumerations in one place.
"""

from enum import Enum, auto

class MessageMode(Enum):
    """Message delivery modes."""
    NORMAL = auto()      # Standard delivery
    BROADCAST = auto()   # Send to all agents
    DIRECT = auto()      # Direct delivery, no routing
    QUEUED = auto()      # Queue for later delivery
    PRIORITY = auto()    # High-priority delivery
    BULK = auto()        # Batch delivery
    SYSTEM = auto()      # System-level message
    RESUME = auto()      # Resume operation
    SYNC = auto()        # Synchronize state
    VERIFY = auto()      # Verify operation
    REPAIR = auto()      # Repair operation
    BACKUP = auto()      # Backup operation
    RESTORE = auto()     # Restore operation
    CLEANUP = auto()     # Cleanup operation
    CAPTAIN = auto()     # Captain operation
    TASK = auto()        # Task operation
    INTEGRATE = auto()   # Integration operation

class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    CRITICAL = 4

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

class MessageType(Enum):
    """Types of messages in the system."""
    COMMAND = auto()     # System command
    RESPONSE = auto()    # Response to a command
    NOTIFICATION = auto() # System notification
    ERROR = auto()       # Error message
    DEBUG = auto()       # Debug information
    STATUS = auto()      # Status update
    DATA = auto()        # Data transfer
    HEARTBEAT = auto()   # Health check 