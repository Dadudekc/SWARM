"""
Rate Limiter Module
-----------------
Provides rate limiting functionality for API calls.
"""

import time
from datetime import datetime
from typing import Dict, Optional, Union, Callable, List
from functools import wraps

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.rate_limits: Dict[str, Dict[str, Union[int, datetime]]] = {}
        self.last_reset: Dict[str, datetime] = {}
        self.calls: Dict[str, int] = {}
        self.timestamps: Dict[str, List[float]] = {}
        self.operation_times: Dict[str, List[float]] = {}  # Track operation timestamps
        self.rate_limit_window = 60  # 1 minute window
        self.max_requests = 30  # 30 requests per minute
        
        # Set default rate limits
        self.default_limits = {
            "post": {"limit": 10, "window": 3600, "remaining": 10},
            "comment": {"limit": 20, "window": 3600, "remaining": 20},
            "login": {"limit": 5, "window": 3600, "remaining": 5}
        }
        
        # Initialize with defaults
        for action, limit_info in self.default_limits.items():
            self.set_rate_limit(action, **limit_info)
    
    def set_rate_limit(
        self,
        action: str,
        limit: int,
        window: int,
        remaining: Optional[int] = None
    ) -> None:
        """Set rate limit for an action.
        
        Args:
            action: Action to limit (e.g. 'post', 'comment')
            limit: Maximum number of calls allowed in window
            window: Time window in seconds
            remaining: Number of remaining calls (defaults to limit)
        """
        self.rate_limits[action] = {
            "limit": limit,
            "window": window,
            "remaining": remaining if remaining is not None else limit
        }
        self.last_reset[action] = datetime.now()
        self.calls[action] = 0
    
    def get_rate_limit(self, action: str) -> Optional[Dict[str, Union[int, datetime]]]:
        """Get rate limit for an action.
        
        Args:
            action: Action to get limit for
            
        Returns:
            Dict with limit, window and remaining, or None if not set
        """
        return self.rate_limits.get(action)
    
    def check_rate_limit(self, operation: str) -> bool:
        """Check if operation is within rate limits.
        
        Args:
            operation: Operation to check rate limit for
            
        Returns:
            True if operation is allowed, False if rate limit exceeded
            
        Raises:
            Exception: If rate limit is exceeded
        """
        # Get rate limit config for operation
        if operation not in self.rate_limits:
            return True  # No rate limit configured
        
        limit_info = self.rate_limits[operation]
        current_time = datetime.now()
        
        # Reset window if expired
        if (current_time - self.last_reset[operation]).total_seconds() > limit_info["window"]:
            self.last_reset[operation] = current_time
            self.calls[operation] = 0
            limit_info["remaining"] = limit_info["limit"]
        
        # Check if limit exceeded
        if limit_info["remaining"] <= 0:
            raise Exception(f"Rate limit exceeded for {operation}")
        
        # Decrement remaining and increment calls
        limit_info["remaining"] -= 1
        self.calls[operation] += 1
        return True
    
    def reset_rate_limit(self, action: str) -> None:
        """Reset rate limit for an action.
        
        Args:
            action: Action to reset
        """
        if action in self.rate_limits:
            self.last_reset[action] = datetime.now()
            self.calls[action] = 0
            self.rate_limits[action]["remaining"] = self.rate_limits[action]["limit"]
    
    def get_remaining_calls(self, action: str) -> int:
        """Get remaining calls for an action.
        
        Args:
            action: Action to check
            
        Returns:
            Number of remaining calls
        """
        if action not in self.rate_limits:
            return 0
            
        limit_info = self.rate_limits[action]
        
        # Reset window if expired
        if (datetime.now() - self.last_reset[action]).total_seconds() > limit_info["window"]:
            return limit_info["limit"]
            
        return max(0, limit_info["limit"] - self.calls[action])
    
    def rate_limit(self, action: str) -> Callable:
        """Decorator to apply rate limiting to a function.
        
        Args:
            action: Action to limit
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.check_rate_limit(action):
                    raise Exception(f"Rate limit exceeded for {action}")
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate limit" in str(e).lower():
                        raise Exception(f"Rate limit exceeded for {action}")
                    raise
            return wrapper
        return decorator

    def _is_within_rate_limit(self, action: str) -> bool:
        """Check if the action is within the rate limit window and update counters."""
        if action not in self.rate_limits:
            return True
        limit_info = self.rate_limits[action]
        current_time = datetime.now()
        # Reset window if expired
        if (current_time - self.last_reset[action]).total_seconds() > limit_info["window"]:
            self.last_reset[action] = current_time
            self.calls[action] = 0
            limit_info["remaining"] = limit_info["limit"]
            return True
        # Check if limit exceeded
        if limit_info["remaining"] <= 0:
            return False
        # Decrement remaining and increment calls
        limit_info["remaining"] -= 1
        self.calls[action] += 1
        return True

# Create a default rate limiter instance
_default_limiter = RateLimiter()

def rate_limit(action: str) -> Callable:
    """Standalone decorator to apply rate limiting to a function.
    
    Args:
        action: Action to limit
        
    Returns:
        Decorated function
    """
    return _default_limiter.rate_limit(action) 
