"""
Base Health Monitoring
--------------------
Base class for health monitoring implementations.
"""

import json
import logging
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health status data."""
    is_healthy: bool = True
    last_check: float = 0.0
    session_active: bool = True
    message_count: int = 0
    error: Optional[str] = None
    metrics: Dict = None
    
    def __post_init__(self):
        """Initialize metrics if not provided."""
        if self.metrics is None:
            self.metrics = {
                "success_rate": 100.0,
                "average_processing_time": 0.0,
                "last_run": datetime.now().isoformat()
            }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check,
            "session_active": self.session_active,
            "message_count": self.message_count,
            "error": self.error,
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HealthStatus':
        """Create from dictionary."""
        return cls(**data)

class BaseHealthMonitor:
    """Base class for health monitoring."""
    
    def __init__(self, 
                 check_interval: int = 300,
                 health_file: str = "health.json"):
        """Initialize the health monitor.
        
        Args:
            check_interval: Seconds between health checks
            health_file: Path to health status file
        """
        self.check_interval = check_interval
        self.health_file = Path(health_file)
        self.health = self._load_health()
    
    def _load_health(self) -> HealthStatus:
        """Load health status from file."""
        try:
            if self.health_file.exists():
                with open(self.health_file, 'r') as f:
                    return HealthStatus.from_dict(json.load(f))
        except Exception as e:
            logger.error(f"Error loading health status: {e}")
        return HealthStatus()
    
    def _save_health(self):
        """Save health status to file."""
        try:
            self.health_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.health_file, 'w') as f:
                json.dump(self.health.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving health status: {e}")
    
    def update_health(self,
                     is_healthy: bool = True,
                     session_active: bool = True,
                     message_count: Optional[int] = None,
                     error: Optional[str] = None,
                     metrics: Optional[Dict] = None):
        """Update health status.
        
        Args:
            is_healthy: Whether system is healthy
            session_active: Whether session is active
            message_count: New message count
            error: Error message
            metrics: Updated metrics
        """
        self.health.is_healthy = is_healthy
        self.health.last_check = time.time()
        self.health.session_active = session_active
        
        if message_count is not None:
            self.health.message_count = message_count
        if error is not None:
            self.health.error = error
        if metrics is not None:
            self.health.metrics.update(metrics)
            
        self._save_health()
    
    def is_healthy(self) -> bool:
        """Check if system is healthy.
        
        Returns:
            Whether system is healthy
        """
        return (
            self.health.is_healthy and
            self.health.session_active and
            time.time() - self.health.last_check < self.check_interval
        )
    
    def get_health_status(self) -> Dict:
        """Get current health status.
        
        Returns:
            Dictionary containing health status
        """
        return self.health.to_dict()
    
    async def start(self):
        """Start health monitoring."""
        self.update_health()
        logger.info("Health monitoring started")
    
    async def stop(self):
        """Stop health monitoring."""
        self.update_health(is_healthy=False, session_active=False)
        logger.info("Health monitoring stopped") 
