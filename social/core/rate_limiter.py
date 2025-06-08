from datetime import datetime, timedelta
from typing import Dict, Any, Callable

class TimeProvider:
    """Time provider for rate limiter."""
    @staticmethod
    def now() -> datetime:
        """Get current time."""
        return datetime.now()

class RateLimiter:
    """Rate limiter implementation for social media platforms."""
    def __init__(self, limits: Dict[str, Dict[str, int]], time_provider: Callable[[], datetime] = TimeProvider.now):
        self.limits = limits
        self.usage = {} 
        self.time_provider = time_provider
    
    def check_limit(self, endpoint: str) -> bool:
        if endpoint not in self.limits:
            # In a real scenario, might log a warning or use a default limit
            # For a stub, let's assume unknown endpoints are not limited or raise error
            # raise ValueError(f"Unknown endpoint: {endpoint}") 
            return True # Or False, depending on desired stub behavior
            
        current_time = self.time_provider()
        if endpoint not in self.usage or current_time >= self.usage[endpoint]['reset_time']:
            self.usage[endpoint] = {
                'count': 0,
                'reset_time': current_time + timedelta(seconds=self.limits[endpoint]['window'])
            }
        if self.usage[endpoint]['count'] >= self.limits[endpoint]['limit']:
            return False
        return True
    
    def record_usage(self, endpoint: str) -> None:
        if endpoint not in self.limits:
            # raise ValueError(f"Unknown endpoint: {endpoint}")
            return # Or handle as per stub requirement
            
        current_time = self.time_provider()
        if endpoint not in self.usage or current_time >= self.usage[endpoint]['reset_time']:
            self.usage[endpoint] = {
                'count': 0,
                'reset_time': current_time + timedelta(seconds=self.limits[endpoint]['window'])
            }
        self.usage[endpoint]['count'] += 1
    
    def get_usage(self, endpoint: str) -> Dict[str, Any]:
        if endpoint not in self.limits:
            # raise ValueError(f"Unknown endpoint: {endpoint}")
            return {} # Or handle as per stub requirement

        current_time = self.time_provider()
        if endpoint not in self.usage or current_time >= self.usage[endpoint]['reset_time']:
            self.usage[endpoint] = {
                'count': 0,
                'reset_time': current_time + timedelta(seconds=self.limits[endpoint]['window'])
            }
        return {
            'limit': self.limits[endpoint]['limit'],
            'remaining': self.limits[endpoint]['limit'] - self.usage[endpoint]['count'],
            'reset': self.usage[endpoint]['reset_time'].timestamp()
        } 
