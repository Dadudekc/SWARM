"""
Error Tracker
------------
Tracks and manages errors in the system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from dreamos.core.autonomy.error.base import TrackedError, ErrorSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorTracker:
    """Tracks and manages errors in the system."""
    
    def __init__(self, max_errors: int = 1000):
        """Initialize the error tracker.
        
        Args:
            max_errors: Maximum number of errors to track
        """
        self.errors: List[TrackedError] = []
        self.max_errors = max_errors
        self.error_counts: Dict[str, int] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = 3
    
    def track_error(self, error: TrackedError) -> None:
        """Track a new error.
        
        Args:
            error: Error to track
        """
        # Add error to list
        self.errors.append(error)
        
        # Update error counts
        self.error_counts[error.error_type] = self.error_counts.get(error.error_type, 0) + 1
        
        # Trim old errors if needed
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log error
        logger.error(f"Error tracked: {error.error_type} - {error.message}")
    
    def get_error_count(self, error_type: str) -> int:
        """Get count of errors of a specific type.
        
        Args:
            error_type: Type of error to count
            
        Returns:
            Count of errors
        """
        return self.error_counts.get(error_type, 0)
    
    def get_recent_errors(self, 
                         error_type: Optional[str] = None,
                         severity: Optional[ErrorSeverity] = None,
                         time_window: Optional[timedelta] = None) -> List[TrackedError]:
        """Get recent errors matching criteria.
        
        Args:
            error_type: Optional error type to filter by
            severity: Optional severity to filter by
            time_window: Optional time window to filter by
            
        Returns:
            List of matching errors
        """
        errors = self.errors
        
        if error_type:
            errors = [e for e in errors if e.error_type == error_type]
            
        if severity:
            errors = [e for e in errors if e.severity == severity]
            
        if time_window:
            cutoff = datetime.now() - time_window
            errors = [e for e in errors if e.timestamp > cutoff]
            
        return errors 