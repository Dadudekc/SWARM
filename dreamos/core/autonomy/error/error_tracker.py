"""
Error Tracker
------------
Tracks and manages error states for agents and operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum, auto

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class ErrorTracker:
    """Tracks and manages error states."""
    
    def __init__(self, max_errors: int = 1000, error_window: int = 3600):
        """Initialize error tracker.
        
        Args:
            max_errors: Maximum number of errors to track
            error_window: Error window in seconds
        """
        self.max_errors = max_errors
        self.error_window = error_window
        self._errors = []
        self._successes = {}
    
    def record_error(self, error_type: str, message: str, severity: ErrorSeverity,
                    agent_id: str, context: Optional[Dict[str, Any]] = None):
        """Record an error.
        
        Args:
            error_type: Type of error
            message: Error message
            severity: Error severity
            agent_id: Agent ID
            context: Optional error context
        """
        error = {
            "type": error_type,
            "message": message,
            "severity": severity,
            "agent_id": agent_id,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self._errors.append(error)
        
        # Trim old errors
        if len(self._errors) > self.max_errors:
            self._errors = self._errors[-self.max_errors:]
    
    def record_success(self, agent_id: str):
        """Record a successful operation.
        
        Args:
            agent_id: Agent ID
        """
        self._successes[agent_id] = datetime.now().isoformat()
    
    def can_execute(self, agent_id: str) -> bool:
        """Check if an agent can execute.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if agent can execute, False otherwise
        """
        # Get recent errors for agent
        recent_errors = [
            e for e in self._errors
            if e["agent_id"] == agent_id and
            datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(seconds=self.error_window)
        ]
        
        # Check error severity
        if any(e["severity"] == ErrorSeverity.CRITICAL for e in recent_errors):
            return False
        
        # Check error count
        if len(recent_errors) >= 5:
            return False
        
        return True
    
    def get_error_summary(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get error summary.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Error summary
        """
        errors = self._errors
        if agent_id:
            errors = [e for e in errors if e["agent_id"] == agent_id]
        
        return {
            "total_errors": len(errors),
            "critical_errors": len([e for e in errors if e["severity"] == ErrorSeverity.CRITICAL]),
            "high_errors": len([e for e in errors if e["severity"] == ErrorSeverity.HIGH]),
            "medium_errors": len([e for e in errors if e["severity"] == ErrorSeverity.MEDIUM]),
            "low_errors": len([e for e in errors if e["severity"] == ErrorSeverity.LOW]),
            "recent_errors": [
                e for e in errors
                if datetime.fromisoformat(e["timestamp"]) > datetime.now() - timedelta(seconds=self.error_window)
            ]
        } 