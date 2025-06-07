"""
Error Handler
------------
Handles error recovery and retry logic.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum, auto

from .error_tracker import ErrorTracker, ErrorSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Retry strategies."""
    NONE = auto()
    LINEAR = auto()
    EXPONENTIAL = auto()
    FIBONACCI = auto()

class ErrorHandler:
    """Handles error recovery and retry logic."""
    
    def __init__(self, error_tracker: ErrorTracker, max_retries: int = 3,
                 retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL):
        """Initialize error handler.
        
        Args:
            error_tracker: Error tracker instance
            max_retries: Maximum retry attempts
            retry_strategy: Retry strategy
        """
        self.error_tracker = error_tracker
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy
        self._retry_counts = {}
    
    async def handle_error(self, error: Exception, agent_id: str,
                          operation: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle an error.
        
        Args:
            error: Exception that occurred
            agent_id: Agent ID
            operation: Operation name
            context: Optional error context
            
        Returns:
            True if should retry, False otherwise
        """
        # Record error
        self.error_tracker.record_error(
            error_type=type(error).__name__,
            message=str(error),
            severity=self._get_error_severity(error),
            agent_id=agent_id,
            context={
                "operation": operation,
                "context": context or {}
            }
        )
        
        # Check if should retry
        if not self._should_retry(agent_id, operation):
            return False
        
        # Calculate retry delay
        delay = self._calculate_retry_delay(agent_id, operation)
        
        # Wait for retry
        await asyncio.sleep(delay)
        
        return True
    
    def _get_error_severity(self, error: Exception) -> ErrorSeverity:
        """Get error severity.
        
        Args:
            error: Exception
            
        Returns:
            Error severity
        """
        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.LOW
        elif isinstance(error, (IOError, OSError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (RuntimeError, NotImplementedError)):
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.CRITICAL
    
    def _should_retry(self, agent_id: str, operation: str) -> bool:
        """Check if should retry.
        
        Args:
            agent_id: Agent ID
            operation: Operation name
            
        Returns:
            True if should retry, False otherwise
        """
        key = f"{agent_id}:{operation}"
        if key not in self._retry_counts:
            self._retry_counts[key] = 0
        
        return self._retry_counts[key] < self.max_retries
    
    def _calculate_retry_delay(self, agent_id: str, operation: str) -> float:
        """Calculate retry delay.
        
        Args:
            agent_id: Agent ID
            operation: Operation name
            
        Returns:
            Retry delay in seconds
        """
        key = f"{agent_id}:{operation}"
        retry_count = self._retry_counts[key]
        self._retry_counts[key] += 1
        
        if self.retry_strategy == RetryStrategy.NONE:
            return 0
        elif self.retry_strategy == RetryStrategy.LINEAR:
            return retry_count * 1.0
        elif self.retry_strategy == RetryStrategy.EXPONENTIAL:
            return 2 ** retry_count
        elif self.retry_strategy == RetryStrategy.FIBONACCI:
            a, b = 1, 1
            for _ in range(retry_count):
                a, b = b, a + b
            return float(a)
        else:
            return 0
    
    async def with_retry(self, operation: str, agent_id: str,
                        func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with retry logic.
        
        Args:
            operation: Operation name
            agent_id: Agent ID
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if not await self.handle_error(e, agent_id, operation):
                    raise 