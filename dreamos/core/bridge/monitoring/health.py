"""
Bridge Health Monitor
------------------
Monitors the health of the bridge system.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import os
import time
from dataclasses import dataclass
from dreamos.core.utils.json_utils import load_json, save_json
from dreamos.core.utils.file_ops import ensure_dir
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.exceptions import FileOpsError
from dreamos.core.utils.core_utils import get_timestamp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BridgeHealth:
    """Bridge health status."""
    is_healthy: bool
    last_check: float
    error_count: int
    last_error: Optional[str] = None
    details: Optional[Dict] = None
    start_time: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    total_failures: int = 0

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.last_success is None:
            self.last_success = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": "healthy" if self.consecutive_failures == 0 else "unhealthy",
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "last_check": self.last_check,
            "last_success": self.last_success.isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "failure_rate": (
                self.total_failures / self.total_checks
                if self.total_checks > 0 else 0.0
            ),
            "error_count": self.error_count,
            "last_error": self.last_error,
            "details": self.details
        }

class BridgeMonitor:
    """Monitors bridge health and status."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.health_file = self.config_path / "health.json"
        self._load_health()
    
    def _load_health(self) -> None:
        """Load health status from file."""
        if self.health_file.exists():
            try:
                with open(self.health_file, 'r') as f:
                    data = json.load(f)
                    self.health = BridgeHealth(**data)
            except Exception:
                self.health = BridgeHealth(False, time.time(), 0)
        else:
            self.health = BridgeHealth(False, time.time(), 0)
    
    def _save_health(self) -> None:
        """Save health status to file."""
        os.makedirs(self.config_path, exist_ok=True)
        with open(self.health_file, 'w') as f:
            json.dump(self.health.to_dict(), f, indent=2)
    
    async def update_health(self, is_healthy: bool, error: Optional[str] = None) -> None:
        """Update bridge health status."""
        self.health.is_healthy = is_healthy
        self.health.last_check = time.time()
        if error:
            self.health.error_count += 1
            self.health.last_error = error
            self.health.consecutive_failures += 1
            self.health.total_failures += 1
        else:
            self.health.consecutive_failures = 0
            self.health.last_success = datetime.now()
        self.health.total_checks += 1
        self._save_health()
    
    def is_healthy(self) -> bool:
        """Check if bridge is healthy."""
        return (
            self.health.consecutive_failures == 0 and
            datetime.now() - self.health.last_success < timedelta(minutes=5)
        )
    
    def get_health_status(self) -> BridgeHealth:
        """Get current health status."""
        return self.health

__all__ = ['BridgeMonitor', 'BridgeHealth'] 