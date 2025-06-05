"""
Retry Utility Module
------------------
Provides retry functionality for Dream.OS operations.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, Type, Union

logger = logging.getLogger("retry")

def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception
) -> Callable:
    """Decorator for retrying failed operations.
    
    Args:
        max_retries: Maximum number of retries
        backoff_factor: Exponential backoff factor
        exceptions: Exception types to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed. "
                            f"Last error: {e}"
                        )
                        raise last_exception
            
            # This should never be reached due to the raise in the loop
            raise last_exception
        
        return wrapper
    
    return decorator 