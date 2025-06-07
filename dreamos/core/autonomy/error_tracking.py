"""
Error Tracking and Resilience
---------------------------
Tracks errors, implements circuit breakers, and manages retry logic for the response loop system.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Type
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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

@dataclass
class ArchiveError(TrackedError):
    """Error related to archiving operations."""
    error_type: str = "archive_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.MEDIUM

@dataclass
class PromptFormatError(TrackedError):
    """Error related to prompt formatting."""
    error_type: str = "prompt_format_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.HIGH

@dataclass
class AgentInactivityError(TrackedError):
    """Error related to agent inactivity."""
    error_type: str = "agent_inactivity_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.MEDIUM

@dataclass
class DevlogWriteError(TrackedError):
    """Error related to devlog writing."""
    error_type: str = "devlog_write_error"
    
    def __post_init__(self):
        """Set default severity if not specified."""
        if not self.severity:
            self.severity = ErrorSeverity.LOW

class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    QUARANTINE = "quarantine"
    FALLBACK = "fallback"
    ARCHIVE = "archive"
    MANUAL = "manual"

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

class ErrorTracker:
    """Tracks errors and provides error analysis."""
    
    def __init__(self, 
                 max_errors: int = 1000,
                 error_window: int = 3600,
                 failure_vault_path: str = "data/failure_vault"):
        """Initialize the error tracker.
        
        Args:
            max_errors: Maximum number of errors to track
            error_window: Time window for error analysis in seconds
            failure_vault_path: Path to store unfixable errors
        """
        self.max_errors = max_errors
        self.error_window = error_window
        self.failure_vault_path = Path(failure_vault_path)
        self.failure_vault_path.mkdir(parents=True, exist_ok=True)
        
        self.errors: deque[TrackedError] = deque(maxlen=max_errors)
        self.circuit_breakers: Dict[str, CircuitBreaker] = defaultdict(
            lambda: CircuitBreaker()
        )
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}
    
    def record_error(self, 
                    error: TrackedError,
                    recovery_strategy: Optional[RecoveryStrategy] = None):
        """Record an error occurrence.
        
        Args:
            error: Error to record
            recovery_strategy: Optional recovery strategy
        """
        self.errors.append(error)
        
        # Update circuit breaker
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.circuit_breakers[error.agent_id].record_failure()
        
        # Set recovery strategy
        if recovery_strategy:
            self.recovery_strategies[error.agent_id] = recovery_strategy
        
        logger.error(
            f"Error recorded: {error.error_type} for agent {error.agent_id} - {error.message}",
            extra=error.to_dict()
        )
        
        # Handle unfixable errors
        if error.severity == ErrorSeverity.CRITICAL:
            self._archive_unfixable_error(error)
    
    def record_success(self, agent_id: str):
        """Record a successful operation.
        
        Args:
            agent_id: ID of the agent that succeeded
        """
        self.circuit_breakers[agent_id].record_success()
    
    def can_execute(self, agent_id: str) -> bool:
        """Check if an agent can execute based on circuit breaker state.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            True if the agent can execute, False otherwise
        """
        return self.circuit_breakers[agent_id].can_execute()
    
    def get_error_summary(self, 
                         agent_id: Optional[str] = None,
                         window: Optional[int] = None) -> Dict:
        """Get a summary of recent errors.
        
        Args:
            agent_id: Optional agent ID to filter by
            window: Optional time window in seconds
            
        Returns:
            Dictionary containing error statistics
        """
        now = datetime.now()
        window = window or self.error_window
        
        # Filter errors by time window and agent
        recent_errors = [
            e for e in self.errors
            if (now - e.timestamp).total_seconds() <= window
            and (not agent_id or e.agent_id == agent_id)
        ]
        
        # Count errors by type and severity
        error_types = defaultdict(int)
        severities = defaultdict(int)
        
        for error in recent_errors:
            error_types[error.error_type] += 1
            severities[error.severity.name] += 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": dict(error_types),
            "severities": dict(severities),
            "window_seconds": window,
            "agent_id": agent_id
        }
    
    def get_agent_health(self, agent_id: str) -> Dict:
        """Get health status for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary containing agent health information
        """
        circuit_breaker = self.circuit_breakers[agent_id]
        error_summary = self.get_error_summary(agent_id=agent_id)
        health_metrics = circuit_breaker.get_health_metrics()
        
        # Determine health status
        if circuit_breaker.state == "CLOSED" and circuit_breaker.recovery_streak > 5:
            status = "🟢 healthy"
        elif circuit_breaker.state == "HALF-OPEN":
            status = "🟡 unstable"
        else:
            status = "🔴 failing"
        
        return {
            "agent_id": agent_id,
            "status": status,
            "circuit_state": circuit_breaker.state,
            "health_metrics": health_metrics,
            "error_summary": error_summary,
            "recovery_strategy": self.recovery_strategies.get(agent_id, RecoveryStrategy.RETRY).value
        }
    
    def get_critical_errors(self, 
                           window: Optional[int] = None) -> List[TrackedError]:
        """Get critical errors within a time window.
        
        Args:
            window: Optional time window in seconds
            
        Returns:
            List of critical error records
        """
        now = datetime.now()
        window = window or self.error_window
        
        return [
            e for e in self.errors
            if (now - e.timestamp).total_seconds() <= window
            and e.severity == ErrorSeverity.CRITICAL
        ]
    
    def _archive_unfixable_error(self, error: TrackedError):
        """Archive an unfixable error to the failure vault.
        
        Args:
            error: Error to archive
        """
        try:
            # Create error archive file
            timestamp = error.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{error.agent_id}_{error.error_type}_{timestamp}.json"
            filepath = self.failure_vault_path / filename
            
            # Write error to file
            with open(filepath, 'w') as f:
                json.dump(error.to_dict(), f, indent=2)
            
            logger.info(
                f"Archived unfixable error to {filepath}",
                extra={"error": error.to_dict()}
            )
            
        except Exception as e:
            logger.error(f"Failed to archive error: {e}")
    
    def clear_errors(self, agent_id: Optional[str] = None):
        """Clear error history.
        
        Args:
            agent_id: Optional agent ID to clear errors for
        """
        if agent_id:
            self.errors = deque(
                (e for e in self.errors if e.agent_id != agent_id),
                maxlen=self.max_errors
            )
            if agent_id in self.circuit_breakers:
                del self.circuit_breakers[agent_id]
            if agent_id in self.recovery_strategies:
                del self.recovery_strategies[agent_id]
        else:
            self.errors.clear()
            self.circuit_breakers.clear()
            self.recovery_strategies.clear()
    
    def manual_reset(self, agent_id: str):
        """Manually reset an agent's circuit breaker.
        
        Args:
            agent_id: ID of the agent to reset
        """
        if agent_id in self.circuit_breakers:
            self.circuit_breakers[agent_id].manual_reset()
            logger.info(f"Manually reset circuit breaker for agent {agent_id}") 