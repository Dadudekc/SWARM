"""
Message-related enums for Dream.OS.
Consolidates all messaging-related enumerations in one place.
"""

from enum import Enum, auto

class MessageMode(Enum):
    """Modes for message delivery."""
    NORMAL = auto()  # Default mode
    TEXT = auto()
    VOICE = auto()
    IMAGE = auto()
    VIDEO = auto()
    FILE = auto()
    EMBED = auto()

class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

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
