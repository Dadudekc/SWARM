"""
Bridge Health Monitor
-------------------
Monitors the health of the bridge system.
"""

import logging
from typing import Dict, Optional

from dreamos.core.monitoring.health.base import BaseHealthMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeHealthMonitor(BaseHealthMonitor):
    """Monitors the health of the bridge system."""
    
    def __init__(self, 
                 check_interval: int = 300,
                 health_file: str = "data/bridge/health.json"):
        """Initialize the bridge health monitor.
        
        Args:
            check_interval: Seconds between health checks
            health_file: Path to health status file
        """
        super().__init__(check_interval=check_interval, health_file=health_file)
    
    def check_health(self) -> bool:
        """Check if the bridge is healthy.
        
        Returns:
            Whether the bridge is healthy
        """
        # Consider unhealthy if:
        # 1. No activity in last 5 minutes
        # 2. Error rate > 20%
        # 3. Average processing time > 30 seconds
        metrics = self.health.metrics
        
        if not self.health.session_active:
            logger.warning("Bridge session is inactive")
            return False
            
        if metrics["success_rate"] < 80:
            logger.warning(f"Bridge error rate too high: {100 - metrics['success_rate']}%")
            return False
            
        if metrics["average_processing_time"] > 30:
            logger.warning(f"Bridge processing time too high: {metrics['average_processing_time']:.1f}s")
            return False
            
        return True
    
    def update_metrics(self,
                      success_rate: Optional[float] = None,
                      processing_time: Optional[float] = None):
        """Update bridge metrics.
        
        Args:
            success_rate: New success rate
            processing_time: New processing time
        """
        metrics = {}
        if success_rate is not None:
            metrics["success_rate"] = success_rate
        if processing_time is not None:
            metrics["average_processing_time"] = processing_time
            
        self.update_health(metrics=metrics) 