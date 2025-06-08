import pytest
from datetime import datetime, timedelta
# from social.strategies.reddit.rate_limiting.rate_limiter import RedditRateLimiter # Old incorrect import
from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter, rate_limit # Corrected import

@pytest.fixture
def rate_limiter():
    return RateLimiter()

class TestRateLimiter:
    def test_initialization(self, rate_limiter):
        """Test that rate limiter initializes with correct defaults."""
        assert isinstance(rate_limiter.rate_limits, dict)
        assert isinstance(rate_limiter.last_reset, dict)
        assert "post" in rate_limiter.default_limits
        assert "comment" in rate_limiter.default_limits
        assert "login" in rate_limiter.default_limits

    def test_get_rate_limit(self, rate_limiter):
        """Test getting rate limit for an action."""
        # Test non-existent action
        assert rate_limiter.get_rate_limit("nonexistent") is None
        
        # Test existing action
        rate_limiter.set_rate_limit("test_action", limit=10, window=3600, remaining=5)
        expected_limit = {"limit": 10, "window": 3600, "remaining": 5}
        assert rate_limiter.get_rate_limit("test_action") == expected_limit

    def test_set_rate_limit(self, rate_limiter):
        """Test setting rate limit for an action."""
        rate_limiter.set_rate_limit("test_action", limit=10, window=3600, remaining=5)
        
        assert "test_action" in rate_limiter.rate_limits
        expected_limit = {"limit": 10, "window": 3600, "remaining": 5}
        assert rate_limiter.rate_limits["test_action"] == expected_limit
        assert "test_action" in rate_limiter.last_reset
        assert isinstance(rate_limiter.last_reset["test_action"], datetime)

    def test_check_rate_limit_default(self, rate_limiter):
        """Test checking rate limit with default values."""
        # First check should use default limit
        assert rate_limiter.check_rate_limit("post") is True
        assert "post" in rate_limiter.rate_limits
        assert rate_limiter.rate_limits["post"]["remaining"] == 9  # 10 - 1

    def test_check_rate_limit_exceeded(self, rate_limiter):
        """Test checking rate limit when exceeded."""
        # Set limit to 0 remaining
        rate_limiter.set_rate_limit("test_action", limit=1, window=3600, remaining=0)
        assert rate_limiter.check_rate_limit("test_action") is False

    def test_check_rate_limit_window_reset(self, rate_limiter):
        """Test rate limit window reset."""
        # First set up the rate limit
        rate_limiter.set_rate_limit("test_action", limit=1, window=3600, remaining=0)
        
        # Then simulate an expired window by backdating last_reset
        rate_limiter.last_reset["test_action"] = datetime.now() - timedelta(hours=2)
        
        # Should reset and allow request
        assert rate_limiter.check_rate_limit("test_action") is True
        assert rate_limiter.rate_limits["test_action"]["remaining"] == 1  # Reset to limit

    def test_rate_limit_decorator(self, rate_limiter):
        """Test rate limit decorator."""
        class TestClass:
            def __init__(self):
                self.rate_limiter = rate_limiter
            
            @rate_limiter.rate_limit("test_action")
            def test_method(self):
                return True
        
        # Set up rate limiter
        rate_limiter.set_rate_limit("test_action", limit=1, window=3600, remaining=1)
        
        # First call should succeed
        test_obj = TestClass()
        assert test_obj.test_method() is True
        
        # Second call should fail
        with pytest.raises(Exception, match="Rate limit exceeded for test_action"):
            test_obj.test_method()

    def test_check_rate_limit_exceeded():
        """Test rate limit exceeded."""
        rate_limiter = RateLimiter()
        rate_limiter.set_rate_limit("test_action", 1, 1)
        assert rate_limiter.check_rate_limit("test_action") is True
        with pytest.raises(Exception) as exc_info:
            rate_limiter.check_rate_limit("test_action")
        assert str(exc_info.value) == "Rate limit exceeded for test_action" 
