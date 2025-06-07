"""
Test Reddit Rate Limiter
-----------------------
Tests for Reddit rate limiting functionality.
"""

import pytest
from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter
import time
from datetime import datetime, timedelta

@pytest.fixture
def rate_limiter():
    """Create a RateLimiter instance for testing."""
    return RateLimiter()

def test_initialization():
    """Test rate limiter initialization."""
    rate_limiter = RateLimiter()
    assert rate_limiter.rate_limits == {
        'post': {'limit': 10, 'window': 3600, 'remaining': 10},
        'comment': {'limit': 20, 'window': 3600, 'remaining': 20},
        'login': {'limit': 5, 'window': 3600, 'remaining': 5}
    }

def test_custom_limits():
    """Test setting custom rate limits."""
    rate_limiter = RateLimiter()
    rate_limiter.set_rate_limit('test_action', 5, 60)
    assert rate_limiter.rate_limits['test_action'] == {
        'limit': 5,
        'window': 60,
        'remaining': 5
    }

def test_rate_limit_reset():
    """Test rate limit reset functionality."""
    rate_limiter = RateLimiter()
    action = 'post'
    
    # Use up one rate limit
    assert rate_limiter.check_rate_limit(action)
    rate_limiter.rate_limits[action]['remaining'] = 9
    
    # Reset should restore to limit
    rate_limiter.reset_rate_limit(action)
    assert rate_limiter.rate_limits[action]['remaining'] == 10

def test_rate_limit_exhaustion():
    """Test rate limit exhaustion."""
    rate_limiter = RateLimiter()
    action = 'post'
    
    # Use up all rate limits
    for _ in range(10):
        assert rate_limiter.check_rate_limit(action)
    
    # Next call should fail
    with pytest.raises(Exception) as exc_info:
        rate_limiter.check_rate_limit(action)
    assert str(exc_info.value) == f"Rate limit exceeded for {action}"

def test_get_rate_limit(rate_limiter):
    """Test getting rate limit for an action."""
    # Set up a rate limit
    action = "post"
    rate_limiter.rate_limits[action] = {
        "limit": 10,
        "window": 3600,  # 1 hour
        "remaining": 5
    }
    
    limit = rate_limiter.get_rate_limit(action)
    assert limit["limit"] == 10
    assert limit["window"] == 3600
    assert limit["remaining"] == 5

def test_rate_limit_window(rate_limiter):
    """Test rate limit window functionality."""
    action = "post"
    rate_limiter.rate_limits[action] = {
        "limit": 10,
        "window": 3600,
        "remaining": 5
    }
    rate_limiter.last_reset[action] = datetime.now() - timedelta(minutes=30)
    
    # Should still be within window
    assert rate_limiter.check_rate_limit(action) is True
    assert rate_limiter.rate_limits[action]["remaining"] == 4 