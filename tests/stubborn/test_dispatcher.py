"""
Dispatcher Test Suite
--------------------
Tests for the enhanced SocialPlatformDispatcher functionality:
- Retry logic with configurable attempts
- Rate limiting per platform
- Media validation integration
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from social.core.dispatcher import SocialPlatformDispatcher
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel
from dreamos.social.utils.rate_limiter import RateLimiter
from dreamos.social.utils.media_validator import MediaValidator
from social.strategies.reddit.handlers.login_handler import LoginHandler
from social.strategies.reddit.config import RedditConfig
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir
)

@pytest.fixture(autouse=True)
def setup_test_directories():
    """Create necessary test directories."""
    test_log_dir = Path("tests/runtime/logs")
    ensure_dir(test_log_dir)
    yield
    # Cleanup could be added here if needed

@pytest.fixture
def mock_driver():
    """Create a mock Selenium driver."""
    driver = Mock()
    driver.current_url = "https://example.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return RedditConfig(
        username="test_user",
        password="test_pass",
        cookies_path=Path("tests/runtime/cookies"),
        max_retries=3,
        retry_delay=1,
        session_timeout=24,
        rate_limit_posts=10,
        rate_limit_comments=50,
        supported_image_formats=[".jpg", ".png", ".gif"],
        supported_video_formats=[".mp4", ".mov"],
        max_images=10,
        max_videos=1,
        max_video_size=10 * 1024 * 1024
    )

@pytest.fixture
def mock_memory_update():
    """Create a mock memory update dictionary."""
    return {
        "last_error": None,
        "stats": {"login": 0, "post": 0, "comment": 0},
        "last_action": None,
        "retry_history": [],
        "operation_times": {}
    }

@pytest.fixture
def mock_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a mock platform strategy."""
    strategy = Mock()
    strategy.driver = mock_driver
    strategy.config = mock_config
    strategy.memory_updates = mock_memory_update
    strategy.is_logged_in.return_value = False
    strategy.login.return_value = True
    strategy.post.return_value = True
    strategy.create_post.return_value = "Test post content"
    strategy.media_files = []  # Initialize empty media files
    strategy.is_video = False  # Initialize is_video flag
    return strategy

@pytest.fixture
def mock_limits():
    """Create mock rate limits."""
    return {
        'rules': {
            'post': {'limit': 10, 'window': 3600, 'remaining': 10},
            'comment': {'limit': 20, 'window': 3600, 'remaining': 20},
            'login': {'limit': 5, 'window': 3600, 'remaining': 5}
        }
    }

@pytest.fixture
def mock_rate_limiter(mock_limits):
    """Create a mock rate limiter instance."""
    return RateLimiter(config=mock_limits)

@pytest.fixture
def log_manager():
    """Create a LogManager instance for rate limiter logging."""
    return LogManager(LogConfig(
        level=LogLevel.DEBUG,
        log_dir="tests/runtime/logs",
        log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        date_format="%Y-%m-%d %H:%M:%S",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        max_age_days=30,
        platforms={
            "rate_limiter": "rate_limiter.log",
            "dispatcher": "dispatcher.log",
            "social": "social.log"
        }
    ))

class TestDispatcherRetryLogic:
    """Test suite for dispatcher retry functionality."""
    
    def test_retry_on_login_failure(self, mock_driver, mock_config, mock_memory_update, mock_rate_limiter):
        """Test that dispatcher retries on login failure."""
        # Setup mock strategy
        current_memory_update = mock_memory_update.copy() # Ensure a fresh copy
        mock_strategy = Mock()
        
        # Setup login to fail once then succeed
        login_results = [False, True]
        def login_side_effect(*args, **kwargs):
            result = login_results.pop(0)
            print(f"login() called, returns: {result}")
            return result
        mock_strategy.login.side_effect = login_side_effect
        
        # Setup is_logged_in to match login state
        login_state = [False, False, True]
        def is_logged_in_side_effect():
            result = login_state.pop(0)
            print(f"is_logged_in() called, returns: {result}")
            return result
        mock_strategy.is_logged_in.side_effect = is_logged_in_side_effect
        
        mock_strategy.post.return_value = True
        mock_strategy.media_files = []  # No media files to trigger validation
        mock_strategy.is_video = False
        
        # Create dispatcher with mock strategy
        dispatcher = SocialPlatformDispatcher(current_memory_update) # Use the copied memory
        dispatcher.strategies = {"test": mock_strategy}
        dispatcher.platform_configs = {"test": type('PlatformConfig', (), {'config': mock_config})()}
        dispatcher.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher.login_handler = mock_login_handler
        
        # Process platform
        result = dispatcher._process_platform(mock_strategy, "test content", "test")
        
        # Verify behavior
        assert result is True
        assert mock_strategy.login.call_count == 2  # Should retry once
        assert mock_strategy.post.call_count == 1  # Should post after successful login

    def test_max_retries_exceeded(self, mock_driver, mock_config, mock_memory_update):
        """Test that dispatcher stops after max retries."""
        # Setup mock strategy that always fails
        mock_strategy = Mock()
        mock_strategy.login.side_effect = Exception("Login failed")
        mock_strategy.is_logged_in.return_value = False
        mock_strategy.media_files = []
        mock_strategy.is_video = False
        
        # Create dispatcher with mock strategy
        dispatcher = SocialPlatformDispatcher(mock_memory_update)
        dispatcher.strategies = {"test": mock_strategy}
        dispatcher.platform_configs = {"test": Mock(config=mock_config)}
        
        # Mock the rate limiter to always allow
        mock_rate_limiter = Mock()
        mock_rate_limiter.check_rate_limit.return_value = True
        dispatcher.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher.login_handler = mock_login_handler
        
        # Process platform
        result = dispatcher._process_platform(mock_strategy, "test content", "test")
        
        # Verify behavior
        assert result is False
        assert mock_strategy.login.call_count == 3  # Should try max_retries times

class TestDispatcherRateLimiting:
    """Test suite for dispatcher rate limiting functionality."""
    
    def test_rate_limit_respect(self, mock_driver, mock_config, mock_memory_update, mock_rate_limiter):
        """Test that dispatcher respects rate limits."""
        # Setup mock strategy and rate limiter
        current_memory_update = mock_memory_update.copy() # Ensure a fresh copy
        mock_strategy = Mock()
        mock_strategy.login.return_value = True
        mock_strategy.is_logged_in.return_value = True
        mock_strategy.post.return_value = True
        mock_strategy.media_files = []  # No media files to trigger validation
        mock_strategy.is_video = False
        
        # Create dispatcher with mocks
        dispatcher = SocialPlatformDispatcher(current_memory_update) # Use the copied memory
        dispatcher.strategies = {"test": mock_strategy}
        dispatcher.platform_configs = {"test": Mock(config=mock_config)}
        dispatcher.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher.login_handler = mock_login_handler
        
        # Process platform
        result = dispatcher._process_platform(mock_strategy, "test content", "test")
        
        # Verify behavior
        assert result is True
        assert mock_strategy.post.call_count == 1  # Should post successfully

    def test_rate_limit_persistent(self, mock_driver, mock_config, mock_memory_update, mock_rate_limiter):
        """Test that rate limits persist across dispatcher instances."""
        # Setup mock strategy
        current_memory_update = mock_memory_update.copy() # Ensure a fresh copy
        mock_strategy = Mock()
        mock_strategy.login.return_value = True
        mock_strategy.is_logged_in.return_value = True
        mock_strategy.post.return_value = True
        mock_strategy.media_files = []  # No media files to trigger validation
        mock_strategy.is_video = False
        
        # Create first dispatcher
        dispatcher1 = SocialPlatformDispatcher(current_memory_update)
        dispatcher1.strategies = {"test": mock_strategy}
        dispatcher1.platform_configs = {"test": Mock(config=mock_config)}
        dispatcher1.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher1.login_handler = mock_login_handler
        
        # Process platform with first dispatcher
        result1 = dispatcher1._process_platform(mock_strategy, "test content", "test")
        assert result1 is True
        
        # Create second dispatcher with same rate limiter
        dispatcher2 = SocialPlatformDispatcher(current_memory_update)
        dispatcher2.strategies = {"test": mock_strategy}
        dispatcher2.platform_configs = {"test": Mock(config=mock_config)}
        dispatcher2.rate_limiter = mock_rate_limiter
        dispatcher2.login_handler = mock_login_handler
        
        # Process platform with second dispatcher
        result2 = dispatcher2._process_platform(mock_strategy, "test content", "test")
        assert result2 is True
        
        # Verify rate limits were respected
        assert mock_rate_limiter.check_rate_limit.call_count == 2

class TestDispatcherMediaValidation:
    """Test suite for dispatcher media validation functionality."""
    
    def test_valid_media_processing(self, mock_strategy, mock_config, mock_memory_update):
        """Test that valid media is processed correctly."""
        # Setup mock strategy with valid media
        mock_strategy.media_files = ["test.jpg"]
        mock_strategy.is_video = False
        
        # Create dispatcher
        dispatcher = SocialPlatformDispatcher(mock_memory_update)
        dispatcher.strategies = {"test": mock_strategy}
        dispatcher.platform_configs = {"test": Mock(config=mock_config)}
        
        # Mock the rate limiter to always allow
        mock_rate_limiter = Mock()
        mock_rate_limiter.check_rate_limit.return_value = True
        dispatcher.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher.login_handler = mock_login_handler
        
        # Process platform
        result = dispatcher._process_platform(mock_strategy, "test content", "test")
        
        # Verify behavior
        assert result is True
        assert mock_strategy.post.call_count == 1  # Should post successfully

    def test_invalid_media_rejection(self, mock_strategy, mock_config, mock_memory_update, mock_rate_limiter):
        """Test that invalid media is rejected."""
        # Setup mock strategy with invalid media
        mock_strategy.media_files = ["test.exe"]  # Unsupported format
        mock_strategy.is_video = False
        
        # Create dispatcher
        dispatcher = SocialPlatformDispatcher(mock_memory_update)
        dispatcher.strategies = {"test": mock_strategy}
        dispatcher.platform_configs = {"test": Mock(config=mock_config)}
        dispatcher.rate_limiter = mock_rate_limiter
        
        # Mock the login handler
        mock_login_handler = Mock()
        mock_login_handler.handle_login.side_effect = lambda strategy, platform, logger: strategy.login()
        dispatcher.login_handler = mock_login_handler
        
        # Process platform
        result = dispatcher._process_platform(mock_strategy, "test content", "test")
        
        # Verify behavior
        assert result is False
        assert mock_strategy.post.call_count == 0  # Should not post 
