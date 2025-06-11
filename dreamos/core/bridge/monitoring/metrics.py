"""
Bridge Metrics
------------
Tracks metrics for bridge operations.
"""

from dreamos.core.utils.json_utils import load_json, save_json
from dreamos.core.utils.file_ops import ensure_dir
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.exceptions import FileOpsError
from dreamos.core.utils.core_utils import get_timestamp

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BridgeHealth:
    """Tracks bridge health status."""
    
    def __init__(
        self,
        is_healthy: bool = True,
        last_check: Optional[datetime] = None,
        error_count: int = 0
    ):
        """Initialize bridge health.
        
        Args:
            is_healthy: Whether bridge is healthy
            last_check: Last health check timestamp
            error_count: Number of errors
        """
        self.is_healthy = is_healthy
        self.last_check = last_check or datetime.now()
        self.error_count = error_count
        
    def update(self, is_healthy: bool, error_count: Optional[int] = None) -> None:
        """Update health status.
        
        Args:
            is_healthy: Whether bridge is healthy
            error_count: Optional error count
        """
        self.is_healthy = is_healthy
        self.last_check = datetime.now()
        if error_count is not None:
            self.error_count = error_count
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat(),
            "error_count": self.error_count
        }

class BridgeMetrics:
    """Tracks metrics for bridge operations."""
    
    def __init__(self):
        """Initialize bridge metrics."""
        self.health = BridgeHealth()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0
        self.last_error = None
        self.start_time = datetime.now()
        
    def update_metrics(
        self,
        success: bool,
        response_time: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Update metrics.
        
        Args:
            success: Whether request was successful
            response_time: Optional response time
            error: Optional error message
        """
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            if response_time is not None:
                self.average_response_time = (
                    (self.average_response_time * (self.successful_requests - 1) +
                     response_time) / self.successful_requests
                )
        else:
            self.failed_requests += 1
            self.last_error = error
            self.health.update(False, self.failed_requests)
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Dictionary containing metrics
        """
        return {
            "health": self.health.to_dict(),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_response_time": self.average_response_time,
            "last_error": self.last_error,
            "uptime": (datetime.now() - self.start_time).total_seconds()
        } 