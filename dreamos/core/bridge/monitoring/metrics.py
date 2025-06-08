"""
Bridge Metrics
------------
Collects and manages metrics for the bridge system.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeMetrics:
    """Collects and manages bridge metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_successes = 0
        self.total_errors = 0
        self.error_types = defaultdict(int)
        self.response_times: List[float] = []
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        
    def record_request(self) -> None:
        """Record a new request."""
        self.total_requests += 1
        
    def record_success(self, response_time: float = 0.0) -> None:
        """Record a successful request.
        
        Args:
            response_time: Response time in seconds
        """
        self.total_successes += 1
        self.response_times.append(response_time)
        
    def record_error(self, error: str) -> None:
        """Record an error.
        
        Args:
            error: Error message
        """
        self.total_errors += 1
        self.error_types[error] += 1
        self.last_error = error
        self.last_error_time = datetime.now()
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Metrics dictionary
        """
        # Calculate average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        
        # Calculate error rate
        error_rate = (
            self.total_errors / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_errors": self.total_errors,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "error_types": dict(self.error_types),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "uptime": (datetime.now() - self.start_time).total_seconds()
        }
        
    def reset(self) -> None:
        """Reset all metrics."""
        self.__init__() 