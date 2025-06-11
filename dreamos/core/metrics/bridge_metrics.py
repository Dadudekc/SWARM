"""
Bridge Metrics Module
------------------
Specialized metrics for bridge operations.
"""

from typing import Dict, Optional
from datetime import datetime
from .base import BaseMetrics

class BridgeMetrics(BaseMetrics):
    """Metrics for bridge operations."""
    
    def __init__(self, metrics_dir: Optional[str] = None):
        """Initialize bridge metrics.
        
        Args:
            metrics_dir: Optional directory to store metrics
        """
        super().__init__("bridge_metrics", metrics_dir)
        self.last_request: Optional[datetime] = None
        self.last_error: Optional[datetime] = None
        
    def record_request(self, bridge_type: str, operation: str) -> None:
        """Record a bridge request.
        
        Args:
            bridge_type: Type of bridge (e.g. 'discord', 'telegram')
            operation: Operation type
        """
        self.increment("bridge_requests", tags={
            "bridge": bridge_type,
            "operation": operation
        })
        self.last_request = datetime.now()
        
    def record_success(self, bridge_type: str, operation: str, duration: float) -> None:
        """Record a successful bridge operation.
        
        Args:
            bridge_type: Type of bridge
            operation: Operation type
            duration: Operation duration in seconds
        """
        self.increment("bridge_successes", tags={
            "bridge": bridge_type,
            "operation": operation
        })
        self.histogram("bridge_duration", duration, tags={
            "bridge": bridge_type,
            "operation": operation
        })
        
    def record_error(self, bridge_type: str, operation: str, error: str) -> None:
        """Record a bridge error.
        
        Args:
            bridge_type: Type of bridge
            operation: Operation type
            error: Error message
        """
        self.increment("bridge_errors", tags={
            "bridge": bridge_type,
            "operation": operation
        })
        self.last_error = datetime.now()
        
    def get_metrics(self) -> Dict:
        """Get current metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "last_request": self.last_request.isoformat() if self.last_request else None,
            "last_error": self.last_error.isoformat() if self.last_error else None
        })
        return metrics 