from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
import time

class RateLimiter:
    """Manages rate limits for Reddit API operations."""
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.last_reset: Dict[str, datetime] = {}
        
        # Default Reddit rate limits
        self.default_limits = {
            "post": {"limit": 10, "window": 3600},  # 10 posts per hour
            "comment": {"limit": 50, "window": 3600},  # 50 comments per hour
            "login": {"limit": 5, "window": 3600}  # 5 login attempts per hour
        }
        
    def get_rate_limit(self, action: str) -> Optional[Dict[str, Any]]:
        """Get the current rate limit for an action.
        
        Args:
            action: The action to get the rate limit for
            
        Returns:
            The rate limit information or None if not set
        """
        return self.rate_limits.get(action)
        
    def set_rate_limit(self, action: str, limit_info: Dict[str, Any]) -> None:
        """Set a custom rate limit for an action.
        
        Args:
            action: The action to set the rate limit for
            limit_info: Dictionary containing limit, window, and remaining
        """
        self.rate_limits[action] = limit_info
        if action not in self.last_reset:
            self.last_reset[action] = datetime.now()
            
    def check_rate_limit(self, action: str) -> bool:
        """Check if rate limit is exceeded for an action.
        
        Args:
            action: Action to check rate limit for
            
        Returns:
            bool: True if rate limit is not exceeded, False otherwise
        """
        if action not in self.rate_limits:
            # Initialize with default limit if not set
            self.set_rate_limit(action, {
                "limit": self.default_limits[action]["limit"],
                "window": self.default_limits[action]["window"],
                "window_start": time.time(),
                "remaining": self.default_limits[action]["limit"]
            })
            
        current_time = time.time()
        limit_info = self.rate_limits[action]
        
        # Initialize remaining to limit if not set
        if "remaining" not in limit_info:
            limit_info["remaining"] = limit_info["limit"]
            
        # Reset window if expired
        if current_time - limit_info["window_start"] >= limit_info["window"]:
            limit_info["remaining"] = limit_info["limit"]
            limit_info["window_start"] = current_time
            return True
            
        # Check if rate limit is exceeded
        if limit_info["remaining"] <= 0:
            return False
            
        limit_info["remaining"] -= 1
        return True
        
def rate_limit(action: str):
    """Decorator to apply rate limiting to a function.
    
    Args:
        action: The action to rate limit
        
    Returns:
        Decorated function that checks rate limits before executing
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.rate_limiter.check_rate_limit(action):
                raise Exception(f"Rate limit exceeded for {action}")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator 