"""
Retry mechanism implementation with exponential backoff.
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Union, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Base class for retry-related errors."""
    pass

class RetryMechanism:
    """Implements retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
    ):
        """Initialize the retry mechanism.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
            exceptions: Exception type(s) to catch and retry on
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = exceptions
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a specific attempt using exponential backoff.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            Delay in seconds before next retry
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def execute(self, operation: Callable[[], Any]) -> Any:
        """Execute an operation with retry logic.
        
        Args:
            operation: Callable that performs the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            RetryError: If all retry attempts fail
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return operation()
            except self.exceptions as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )
        
        raise RetryError(
            f"Operation failed after {self.max_retries} attempts"
        ) from last_error

def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """Decorator for retrying operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds between retries
        exceptions: Exception type(s) to catch and retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_mechanism = RetryMechanism(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exceptions=exceptions
            )
            return retry_mechanism.execute(lambda: func(*args, **kwargs))
        return wrapper
    return decorator 