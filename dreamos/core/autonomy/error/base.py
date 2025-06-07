"""
Base Error Tracking
-----------------
Base classes for error tracking and circuit breaking.
"""

import json
import logging
import time
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Type
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TrackedError:
    """Base class for tracked errors."""
    timestamp: datetime
    message: str
    severity: ErrorSeverity
    agent_id: str
    context: Dict
    error_type: str = "base_error"
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "severity": self.severity.name,
            "agent_id": self.agent_id,
            "context": self.context,
            "error_type": self.error_type
        }

class CircuitBreaker:
    """Circuit breaker for error rate monitoring."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 reset_timeout: int = 60,
                 half_open_timeout: int = 30,
                 error_decay_rate: float = 0.1):
        """Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Seconds before attempting reset
            half_open_timeout: Seconds in half-open state
            error_decay_rate: Rate at which errors decay over time
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.error_decay_rate = error_decay_rate
        
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.half_open_start = None
        self.recovery_streak = 0
        self.last_success_time = None
    
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        self.recovery_streak = 0
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failures} failures"
            )
    
    def record_success(self):
        """Record a success and potentially close the circuit."""
        if self.state == "HALF-OPEN":
            self.state = "CLOSED"
            self.failures = 0
            self.last_failure_time = None
            self.recovery_streak += 1
            self.last_success_time = datetime.now()
            logger.info("Circuit breaker closed after successful operation")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state."""
        now = datetime.now()
        
        # Apply error decay
        if self.failures > 0 and self.last_failure_time:
            time_since_failure = (now - self.last_failure_time).total_seconds()
            decayed_failures = self.failures * (1 - self.error_decay_rate * time_since_failure)
            self.failures = max(0, decayed_failures)
        
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if not self.last_failure_time:
                return True
            
            if (now - self.last_failure_time).total_seconds() >= self.reset_timeout:
                self.state = "HALF-OPEN"
                self.half_open_start = now
                logger.info("Circuit breaker entering half-open state")
                return True
            
            return False
        
        if self.state == "HALF-OPEN":
            if not self.half_open_start:
                return True
            
            if (now - self.half_open_start).total_seconds() >= self.half_open_timeout:
                self.state = "CLOSED"
                self.failures = 0
                self.last_failure_time = None
                logger.info("Circuit breaker closed after timeout")
                return True
            
            return False
        
        return True
    
    def get_health_metrics(self) -> Dict:
        """Get health metrics for the circuit breaker.
        
        Returns:
            Dictionary containing health metrics
        """
        now = datetime.now()
        uptime = None
        if self.last_success_time:
            uptime = (now - self.last_success_time).total_seconds()
        
        return {
            "state": self.state,
            "failures": self.failures,
            "recovery_streak": self.recovery_streak,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "uptime_seconds": uptime
        }
    
    def manual_reset(self):
        """Manually reset the circuit breaker."""
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = None
        self.half_open_start = None
        logger.info("Circuit breaker manually reset") 