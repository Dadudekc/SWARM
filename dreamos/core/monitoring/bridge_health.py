"""
Bridge Health Monitor Module
--------------------------
Provides health monitoring for Dream.OS bridges.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("bridge_health")

@dataclass
class HealthStatus:
    """Bridge health status."""
    is_healthy: bool = True
    last_check: float = 0.0
    session_active: bool = False
    message_count: int = 0
    error: Optional[str] = None

class BridgeHealthMonitor:
    """Monitors bridge health status."""
    
    def __init__(self, status_file: str, check_interval: int = 30):
        """Initialize health monitor.
        
        Args:
            status_file: Path to status file
            check_interval: Health check interval in seconds
        """
        self.status_file = Path(status_file)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.check_interval = check_interval
        self.health = HealthStatus()
        self._load_health()
    
    def _load_health(self):
        """Load health status from file."""
        try:
            if self.status_file.exists():
                with open(self.status_file) as f:
                    data = json.load(f)
                    self.health = HealthStatus(**data)
        except Exception as e:
            logger.error(f"Failed to load health status: {e}")
            self.health = HealthStatus()
    
    def _save_health(self):
        """Save health status to file."""
        try:
            data = {
                "is_healthy": self.health.is_healthy,
                "last_check": self.health.last_check,
                "session_active": self.health.session_active,
                "message_count": self.health.message_count,
                "error": self.health.error
            }
            with open(self.status_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health status: {e}")
    
    def update_health(
        self,
        is_healthy: bool = True,
        session_active: bool = True,
        message_count: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update health status.
        
        Args:
            is_healthy: Whether bridge is healthy
            session_active: Whether session is active
            message_count: New message count
            error: Error message
        """
        self.health.is_healthy = is_healthy
        self.health.last_check = time.time()
        self.health.session_active = session_active
        if message_count is not None:
            self.health.message_count = message_count
        if error is not None:
            self.health.error = error
        self._save_health()
    
    async def start(self):
        """Start health monitoring."""
        self.update_health()
        logger.info("Health monitoring started")
    
    async def stop(self):
        """Stop health monitoring."""
        self.update_health(is_healthy=False, session_active=False)
        logger.info("Health monitoring stopped")
    
    def is_healthy(self) -> bool:
        """Check if bridge is healthy.
        
        Returns:
            Whether bridge is healthy
        """
        return (
            self.health.is_healthy and
            self.health.session_active and
            time.time() - self.health.last_check < self.check_interval
        ) 