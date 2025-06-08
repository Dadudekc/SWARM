"""
Error Types
----------
Specific error types for different failure scenarios.
"""

from datetime import datetime
from typing import Dict, Optional

from dreamos.core.autonomy.error.base import TrackedError, ErrorSeverity

class ArchiveError(TrackedError):
    """Error related to archiving operations."""
    error_type: str = "archive_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.MEDIUM

class PromptFormatError(TrackedError):
    """Error related to prompt formatting."""
    error_type: str = "prompt_format_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.HIGH

class AgentInactivityError(TrackedError):
    """Error related to agent inactivity."""
    error_type: str = "agent_inactivity_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.MEDIUM

class DevlogWriteError(TrackedError):
    """Error related to devlog writing."""
    error_type: str = "devlog_write_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.LOW

class BridgeConnectionError(TrackedError):
    """Error related to bridge connection."""
    error_type: str = "bridge_connection_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.HIGH

class TaskExecutionError(TrackedError):
    """Error related to task execution."""
    error_type: str = "task_execution_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.HIGH

class ResourceExhaustionError(TrackedError):
    """Error related to resource exhaustion."""
    error_type: str = "resource_exhaustion_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.CRITICAL

class StateTransitionError(TrackedError):
    """Error related to state transitions."""
    error_type: str = "state_transition_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.HIGH

def create_error(error_type: str,
                message: str,
                agent_id: str,
                severity: Optional[ErrorSeverity] = None,
                context: Optional[Dict] = None) -> TrackedError:
    """Create an error of the specified type.
    
    Args:
        error_type: Type of error to create
        message: Error message
        agent_id: ID of the agent that encountered the error
        severity: Optional error severity
        context: Optional error context
        
    Returns:
        Created error instance
    """
    error_classes = {
        "archive_error": ArchiveError,
        "prompt_format_error": PromptFormatError,
        "agent_inactivity_error": AgentInactivityError,
        "devlog_write_error": DevlogWriteError,
        "bridge_connection_error": BridgeConnectionError,
        "task_execution_error": TaskExecutionError,
        "resource_exhaustion_error": ResourceExhaustionError,
        "state_transition_error": StateTransitionError
    }
    
    error_class = error_classes.get(error_type, TrackedError)
    return error_class(
        timestamp=datetime.now(),
        message=message,
        severity=severity,
        agent_id=agent_id,
        context=context or {}
    ) 
