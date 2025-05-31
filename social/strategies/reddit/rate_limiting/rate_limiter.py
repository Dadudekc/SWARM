"""
Rate Limiter Module
-----------------
Provides rate limiting functionality for API calls.
"""

import time
from datetime import datetime
from typing import Dict, Optional, Union, Callable
from functools import wraps

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.rate_limits: Dict[str, Dict[str, Union[int, datetime]]] = {}
        self.last_reset: Dict[str, datetime] = {}
        self.calls: Dict[str, int] = {}
        
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
    
    def check_rate_limit(self, action: str) -> bool:
        """Check if an action is within rate limits.
        
        Args:
            action: Action to check
            
        Returns:
            True if within limits, False if exceeded
        """
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
                return func(*args, **kwargs)
            return wrapper
        return decorator

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