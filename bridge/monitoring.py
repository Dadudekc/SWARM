"""
Bridge Monitoring System
----------------------
Tracks bridge status, metrics, and health checks.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BridgeMetrics:
    """Bridge system metrics."""
    last_run: str
    pending_prompts: int
    last_agent: str
    errors: int
    last_prompt_type: str
    total_processed: int
    success_rate: float
    average_processing_time: float
    last_error: Optional[str] = None
    last_error_time: Optional[str] = None

class BridgeMonitor:
    """Monitors bridge system health and metrics."""
    
    def __init__(self, status_path: str = "runtime/bridge_status.json"):
        """Initialize the bridge monitor."""
        self.status_path = Path(status_path)
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics = self._load_metrics()
        self.processing_times = []
        
    def _load_metrics(self) -> BridgeMetrics:
        """Load existing metrics or create new ones."""
        try:
            if self.status_path.exists():
                with open(self.status_path) as f:
                    data = json.load(f)
                return BridgeMetrics(**data)
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            
        # Default metrics
        return BridgeMetrics(
            last_run=datetime.now().isoformat(),
            pending_prompts=0,
            last_agent="none",
            errors=0,
            last_prompt_type="none",
            total_processed=0,
            success_rate=100.0,
            average_processing_time=0.0
        )
        
    def _save_metrics(self):
        """Save current metrics to file."""
        try:
            with open(self.status_path, 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            
    def update_metrics(self, 
                      agent_id: Optional[str] = None,
                      prompt_type: Optional[str] = None,
                      error: Optional[str] = None,
                      processing_time: Optional[float] = None):
        """Update bridge metrics."""
        self.metrics.last_run = datetime.now().isoformat()
        
        if agent_id:
            self.metrics.last_agent = agent_id
            
        if prompt_type:
            self.metrics.last_prompt_type = prompt_type
            
        if error:
            self.metrics.errors += 1
            self.metrics.last_error = error
            self.metrics.last_error_time = datetime.now().isoformat()
            
        if processing_time is not None:
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 100:  # Keep last 100 times
                self.processing_times.pop(0)
            self.metrics.average_processing_time = sum(self.processing_times) / len(self.processing_times)
            
        # Update success rate
        if self.metrics.total_processed > 0:
            self.metrics.success_rate = (
                (self.metrics.total_processed - self.metrics.errors) / 
                self.metrics.total_processed * 100
            )
            
        self._save_metrics()
        
    def record_prompt_processed(self, success: bool = True):
        """Record a processed prompt."""
        self.metrics.total_processed += 1
        if not success:
            self.metrics.errors += 1
        self._save_metrics()
        
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of bridge status."""
        return {
            "status": "healthy" if self.metrics.errors == 0 else "degraded",
            "metrics": asdict(self.metrics),
            "timestamp": datetime.now().isoformat()
        }
        
    def check_health(self) -> bool:
        """Check if the bridge is healthy."""
        # Consider unhealthy if:
        # 1. No activity in last 5 minutes
        # 2. Error rate > 20%
        # 3. Average processing time > 30 seconds
        last_run = datetime.fromisoformat(self.metrics.last_run)
        time_since_last = (datetime.now() - last_run).total_seconds()
        
        if time_since_last > 300:  # 5 minutes
            logger.warning("Bridge appears stalled - no activity in 5 minutes")
            return False
            
        if self.metrics.success_rate < 80:
            logger.warning(f"Bridge error rate too high: {100 - self.metrics.success_rate}%")
            return False
            
        if self.metrics.average_processing_time > 30:
            logger.warning(f"Bridge processing time too high: {self.metrics.average_processing_time:.1f}s")
            return False
            
        return True 