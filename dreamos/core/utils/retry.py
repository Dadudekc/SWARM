"""
Retry utilities for handling transient failures.
"""

import time
from functools import wraps
from typing import Type, Tuple, Union, Callable, Any

def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,)
) -> Callable:
    """
    Decorator that retries a function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Exception type(s) to catch and retry on
        
    Returns:
        Decorated function that will retry on specified exceptions
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            current_delay = delay
            
            while attempts < max_retries:
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_retries:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
        return wrapper
    return decorator

__all__ = ['with_retry'] 