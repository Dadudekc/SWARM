"""
Retry Utilities

Provides retry mechanisms with exponential backoff and jitter.
"""

import logging
import random
import time
from functools import wraps
from typing import Callable, Type, Union, Tuple, Optional, Any

logger = logging.getLogger('utils.retry')

def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Callable:
    """Decorator for retrying functions with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to increase delay by on each retry
        jitter: Random jitter factor (±jitter * delay)
        exceptions: Exception(s) to catch and retry on
        on_retry: Optional callback function called on each retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Max retry attempts ({max_attempts}) exceeded")
                        raise
                        
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (backoff_factor ** attempt),
                        max_delay
                    )
                    
                    # Add jitter
                    jitter_amount = delay * jitter
                    delay = delay + random.uniform(-jitter_amount, jitter_amount)
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                        
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{max_attempts} "
                        f"after {delay:.1f}s: {str(e)}"
                    )
                    
                    time.sleep(delay)
                    
            raise last_exception
            
        return wrapper
    return decorator

def with_retry(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> Any:
    """Execute a function with retry logic.
    
    Args:
        func: Function to execute
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to increase delay by on each retry
        jitter: Random jitter factor (±jitter * delay)
        exceptions: Exception(s) to catch and retry on
        on_retry: Optional callback function called on each retry
        
    Returns:
        Result of function execution
    """
    return retry(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        exceptions=exceptions,
        on_retry=on_retry
    )(func)

def calculate_retry_delay(
    attempt: int,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1
) -> float:
    """Calculate retry delay with exponential backoff and jitter.
    
    Args:
        attempt: Current attempt number (1-based)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Factor to increase delay by on each retry
        jitter: Random jitter factor (±jitter * delay)
        
    Returns:
        Delay in seconds
    """
    # Calculate base delay with exponential backoff
    delay = initial_delay * (backoff_factor ** (attempt - 1))
    
    # Add jitter
    jitter_amount = delay * jitter
    delay = delay + random.uniform(-jitter_amount, jitter_amount)
    
    # Cap at max delay
    return min(delay, max_delay) 