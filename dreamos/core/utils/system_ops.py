"""
System Operations
--------------
Core system operations and utilities for Dream.OS.
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Tuple

logger = logging.getLogger(__name__)

def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Exception, ...] = (Exception,)
) -> Callable:
    """Decorator for retrying operations.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Delay multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded: {e}")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

def transform_coordinates(x: int, y: int, scale: float = 1.0) -> Tuple[int, int]:
    """Transform screen coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        scale: Scale factor
        
    Returns:
        Transformed (x, y) coordinates
    """
    return (int(x * scale), int(y * scale))

def normalize_coordinates(x: int, y: int, max_x: int, max_y: int) -> Tuple[float, float]:
    """Normalize coordinates to [0,1] range.
    
    Args:
        x: X coordinate
        y: Y coordinate
        max_x: Maximum X value
        max_y: Maximum Y value
        
    Returns:
        Normalized (x, y) coordinates
    """
    return (x / max_x, y / max_y) 
