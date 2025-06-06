"""
Test suite for RateLimiter functionality.
"""

import pytest
import time
from datetime import datetime
from pathlib import Path

from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter
from social.utils.log_manager import LogManager, LogConfig, LogLevel
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir
)

@pytest.fixture
def limiter():
    """Create a RateLimiter instance."""
    return RateLimiter()

@pytest.fixture
def log_manager():
    """Create a LogManager instance for rate limiter logging."""
    return LogManager(LogConfig(
        level=LogLevel.DEBUG,
        log_dir="tests/runtime/logs",
        platforms={"rate_limiter": "rate_limiter.log"}
    ))

def test_default_limits(limiter):
    """Test default rate limits."""
    assert limiter.get_rate_limit("post")["limit"] == 10
    assert limiter.get_rate_limit("post")["window"] == 3600
    assert limiter.get_rate_limit("comment")["limit"] == 20
    assert limiter.get_rate_limit("comment")["window"] == 3600
    assert limiter.get_rate_limit("login")["limit"] == 5
    assert limiter.get_rate_limit("login")["window"] == 3600

def test_set_rate_limit(limiter):
    """Test setting custom rate limit."""
    limiter.set_rate_limit("test", limit=5, window=60)
    limit_info = limiter.get_rate_limit("test")
    assert limit_info["limit"] == 5
    assert limit_info["window"] == 60
    assert limit_info["remaining"] == 5

def test_check_rate_limit(limiter):
    """Test checking rate limit."""
    limiter.set_rate_limit("test", limit=2, window=60)
    assert limiter.check_rate_limit("test") is True
    assert limiter.check_rate_limit("test") is True
    with pytest.raises(Exception) as exc:
        limiter.check_rate_limit("test")
    assert "Rate limit exceeded" in str(exc.value)

def test_reset_rate_limit(limiter):
    """Test resetting rate limit."""
    limiter.set_rate_limit("test", limit=2, window=60)
    assert limiter.check_rate_limit("test") is True
    assert limiter.check_rate_limit("test") is True
    limiter.reset_rate_limit("test")
    assert limiter.check_rate_limit("test") is True
    assert limiter.check_rate_limit("test") is True

def test_get_remaining_calls(limiter):
    """Test getting remaining calls."""
    limiter.set_rate_limit("test", limit=3, window=60)
    assert limiter.get_remaining_calls("test") == 3
    assert limiter.check_rate_limit("test") is True
    assert limiter.get_remaining_calls("test") == 2
    assert limiter.check_rate_limit("test") is True
    assert limiter.get_remaining_calls("test") == 1

def test_rate_limit_decorator(limiter):
    """Test rate limit decorator."""
    @limiter.rate_limit("test")
    def test_func():
        return True

    limiter.set_rate_limit("test", limit=2, window=60)
    assert test_func() is True
    assert test_func() is True
    with pytest.raises(Exception) as exc:
        test_func()
    assert "Rate limit exceeded" in str(exc.value)

def test_window_expiration(limiter):
    """Test rate limit window expiration."""
    limiter.set_rate_limit("test", limit=2, window=1)  # 1 second window
    assert limiter.check_rate_limit("test") is True
    assert limiter.check_rate_limit("test") is True
    time.sleep(1.1)  # Wait for window to expire
    assert limiter.check_rate_limit("test") is True
    assert limiter.check_rate_limit("test") is True

def test_unknown_action(limiter):
    """Test handling of unknown action."""
    assert limiter.get_rate_limit("unknown") is None
    assert limiter.get_remaining_calls("unknown") == 0
    assert limiter.check_rate_limit("unknown") is True  # Unknown actions are not limited 