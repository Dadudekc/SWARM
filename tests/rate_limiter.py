"""
Test suite for social media rate limiter.
Validates token bucket implementation and platform-specific limits.
"""

import pytest
import time
from pathlib import Path
import json
import os

from dreamos.social.rate_limiter import RateLimiter, RateLimitConfig, TokenBucket

@pytest.fixture
def rate_limiter(tmp_path):
    """Create rate limiter with temporary log file."""
    log_file = tmp_path / "test_social_post_log.json"
    return RateLimiter(log_file=str(log_file))

@pytest.fixture
def test_config():
    """Test rate limit configuration."""
    return RateLimitConfig(tokens_per_interval=1, interval_seconds=1)

# Token bucket tests
def test_token_bucket_refill(test_config):
    """Test token bucket refill mechanism."""
    bucket = TokenBucket(test_config)
    
    # Initial state
    assert bucket.tokens == 1.0
    
    # Consume token
    assert bucket.acquire()
    assert bucket.tokens == 0.0
    
    # Wait for refill
    time.sleep(1.1)
    assert bucket.acquire()
    assert bucket.tokens == 0.0

def test_token_bucket_max_tokens(test_config):
    """Test token bucket respects max tokens."""
    bucket = TokenBucket(test_config)
    
    # Wait for multiple refills
    time.sleep(2.1)
    assert bucket.tokens <= test_config.max_tokens

# Platform-specific tests
def test_twitter_rate_limit(rate_limiter):
    """Test Twitter rate limiting (1 post / 5 min)."""
    # First post should succeed
    assert rate_limiter.can_post("twitter")
    
    # Second post should fail
    assert not rate_limiter.can_post("twitter")
    
    # Wait time should be ~5 minutes
    wait_time = rate_limiter.get_wait_time("twitter")
    assert 290 <= wait_time <= 310  # Allow 10s buffer

def test_reddit_rate_limit(rate_limiter):
    """Test Reddit rate limiting (1 post / 10 min)."""
    # First post should succeed
    assert rate_limiter.can_post("reddit")
    
    # Second post should fail
    assert not rate_limiter.can_post("reddit")
    
    # Wait time should be ~10 minutes
    wait_time = rate_limiter.get_wait_time("reddit")
    assert 590 <= wait_time <= 610  # Allow 10s buffer

def test_discord_rate_limit(rate_limiter):
    """Test Discord rate limiting (2 posts / 1 min)."""
    # First two posts should succeed
    assert rate_limiter.can_post("discord")
    assert rate_limiter.can_post("discord")
    
    # Third post should fail
    assert not rate_limiter.can_post("discord")
    
    # Wait time should be ~30 seconds
    wait_time = rate_limiter.get_wait_time("discord")
    assert 25 <= wait_time <= 35  # Allow 5s buffer

# Edge cases
def test_unknown_platform(rate_limiter):
    """Test handling of unknown platforms."""
    assert rate_limiter.can_post("unknown_platform")
    assert rate_limiter.get_wait_time("unknown_platform") == 0.0
    assert rate_limiter.get_platform_stats("unknown_platform") == {}

def test_concurrent_access(rate_limiter):
    """Test concurrent access to rate limiter."""
    import threading
    
    def post_thread():
        return rate_limiter.can_post("twitter")
        
    threads = [threading.Thread(target=post_thread) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # Only one post should succeed
    stats = rate_limiter.get_platform_stats("twitter")
    assert stats["violations"] == 9

# State persistence
def test_state_persistence(tmp_path):
    """Test rate limit state persistence."""
    log_file = tmp_path / "test_social_post_log.json"
    limiter1 = RateLimiter(log_file=str(log_file))
    
    # Make some posts
    limiter1.can_post("twitter")
    limiter1.can_post("reddit")
    
    # Create new limiter with same log file
    limiter2 = RateLimiter(log_file=str(log_file))
    
    # Check state is preserved
    assert not limiter2.can_post("twitter")
    assert not limiter2.can_post("reddit")

# Stats and monitoring
def test_platform_stats(rate_limiter):
    """Test platform statistics tracking."""
    # Make some posts
    rate_limiter.can_post("twitter")
    rate_limiter.can_post("twitter")  # Should fail
    
    stats = rate_limiter.get_platform_stats("twitter")
    assert stats["violations"] == 1
    assert stats["last_violation"] is not None
    assert stats["wait_time"] > 0
    assert stats["tokens"] == 0.0

def test_violation_tracking(rate_limiter):
    """Test violation tracking and reset."""
    # Make multiple violations
    for _ in range(3):
        rate_limiter.can_post("twitter")
        
    stats = rate_limiter.get_platform_stats("twitter")
    assert stats["violations"] == 2  # First post succeeds
    
    # Wait for reset
    time.sleep(1.1)
    assert rate_limiter.can_post("twitter")
    
    stats = rate_limiter.get_platform_stats("twitter")
    assert stats["violations"] == 0
    assert stats["last_violation"] is None 