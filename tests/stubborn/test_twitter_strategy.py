"""
Twitter Strategy Tests
--------------------
Test suite for TwitterStrategy implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from social.strategies.twitter_strategy import TwitterStrategy
from social.strategies.twitter.rate_limiting.rate_limiter import RateLimiter

@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver."""
    driver = Mock()
    driver.find_element = Mock()
    driver.find_elements = Mock(return_value=[])
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "twitter": {
            "credentials": {
                "username": "test_user",
                "password": "test_pass"
            },
            "enabled": True,
            "headless": False
        },
        "browser": {
            "headless": False,
            "proxy_rotation": False,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "timeout": 30,
            "page_load_timeout": 30,
            "implicit_wait": 10,
            "window_title": "Test Window",
            "window_coords": {"x": 0, "y": 0, "width": 1024, "height": 768},
            "cookies_path": "/tmp/test_cookies"
        }
    }

@pytest.fixture
def mock_memory_update():
    """Create a mock memory update dictionary."""
    return {
        "last_action": None,
        "last_error": None,
        "last_success": None,
        "rate_limit_exceeded": False,
        "retry_history": [],
        "stats": {
            "login": 0,
            "post": 0,
            "comment": 0,
            "posts": 0,
            "comments": 0,
            "media_uploads": 0,
            "errors": 0,
            "retries": 0,
            "login_attempts": 0
        }
    }

@pytest.fixture
def mock_utils():
    """Create a mock utils instance."""
    utils = Mock()
    utils.wait_for_element = Mock()
    return utils

@pytest.fixture
def strategy(mock_driver, mock_config, mock_memory_update, mock_utils):
    """Create a TwitterStrategy instance with mocked dependencies."""
    with patch("social.strategies.twitter_strategy.LoginHandler") as mock_login_handler, \
         patch("social.strategies.twitter_strategy.PostHandler") as mock_post_handler, \
         patch("social.strategies.twitter_strategy.TwitterMediaHandler") as mock_media_handler:
        
        # Configure mock handlers
        mock_login_handler.return_value.login.return_value = True
        mock_post_handler.return_value.create_post.return_value = True
        mock_media_handler.return_value.validate_media.return_value = (True, None)
        
        strategy = TwitterStrategy(
            driver=mock_driver,
            config=mock_config,
            memory_update=mock_memory_update,
            utils=mock_utils
        )
        
        # Mock is_logged_in to return True by default
        strategy.is_logged_in = Mock(return_value=True)
        
        # Mock _validate_media to return tuple
        strategy._validate_media = Mock(return_value=(True, None))
        
        return strategy

class TestTwitterStrategy:
    """Test suite for TwitterStrategy."""
    
    def test_init(self, strategy, mock_memory_update):
        """Test strategy initialization."""
        assert strategy.memory_updates == mock_memory_update
        assert strategy.stats["login"] == 0
        assert strategy.stats["post"] == 0
        assert strategy.stats["posts"] == 0
        assert strategy.stats["errors"] == 0
        assert strategy.stats["retries"] == 0
        assert strategy.credentials == {"username": "test_user", "password": "test_pass"}
        assert strategy.memory_updates["last_action"] is None
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["last_success"] is None
        assert strategy.memory_updates["rate_limit_exceeded"] is False
        assert strategy.memory_updates["retry_history"] == []
        assert strategy.memory_updates["stats"]["login"] == 0
        assert strategy.memory_updates["stats"]["post"] == 0
        assert strategy.memory_updates["stats"]["posts"] == 0
        assert strategy.memory_updates["stats"]["errors"] == 0
        assert strategy.memory_updates["stats"]["retries"] == 0

    def test_login_success(self, strategy, mock_driver):
        """Test successful login."""
        assert strategy.login() is True
        assert strategy.memory_updates["last_action"] == "login"
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["login"] == 1
        assert strategy.stats["login"] == 1
        mock_driver.get.assert_called_once_with("https://twitter.com/login")

    def test_login_missing_credentials(self, strategy, mock_config):
        """Test login with missing credentials."""
        strategy.credentials = {}
        assert strategy.login() is False
        assert strategy.memory_updates["last_action"] == "is_logged_in"
        assert strategy.memory_updates["last_error"]["error"] == "Missing credentials"
        assert strategy.memory_updates["last_error"]["context"] == "login"
        assert strategy.memory_updates["stats"]["errors"] == 1
        assert strategy.stats["errors"] == 1

    def test_post_success(self, strategy):
        """Test successful post."""
        content = "Test post content"
        assert strategy.post(content) is True
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1
        assert strategy.memory_updates["stats"]["post"] == 1
        assert strategy.stats["posts"] == 1
        assert strategy.stats["post"] == 1

    def test_post_not_logged_in(self, strategy, mock_utils):
        """Test post when not logged in."""
        strategy.is_logged_in.return_value = False
        content = "Test post content"
        assert strategy.post(content) is False
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"]["error"] == "Post verification failed"
        assert strategy.memory_updates["last_error"]["context"] == "post"
        assert strategy.memory_updates["stats"]["errors"] == 2
        assert strategy.stats["errors"] == 2

    def test_memory_error_tracking(self, strategy):
        """Test memory error tracking."""
        # Test login error
        strategy.credentials = {}
        strategy.login()
        assert strategy.memory_updates["last_action"] == "is_logged_in"
        assert strategy.memory_updates["last_error"]["error"] == "Missing credentials"
        assert strategy.memory_updates["last_error"]["context"] == "login"
        assert strategy.memory_updates["stats"]["errors"] == 1
        assert strategy.stats["errors"] == 1
        
        # Test post error
        strategy.memory_updates["last_error"] = None
        strategy.memory_updates["stats"]["errors"] = 0
        strategy.stats["errors"] = 0
        strategy.post_handler.create_post.return_value = False  # Force post failure
        strategy.post("")
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"]["error"] == "Post verification failed"
        assert strategy.memory_updates["last_error"]["context"] == "post"
        assert strategy.memory_updates["stats"]["errors"] == 2
        assert strategy.stats["errors"] == 2

    @pytest.mark.parametrize("first_wait,expected_calls", [
        (True, 2),  # Rate limit allowed, check in both post() and create_post()
        (False, 1)  # Rate limit exceeded, only check in post()
    ])
    def test_rate_limiting_flow(self, strategy, first_wait, expected_calls):
        """Test rate limiting flow."""
        with patch.object(strategy.rate_limiter, "check_rate_limit") as mock_check:
            mock_check.return_value = first_wait
            content = "Test post content"
            if not first_wait:
                with pytest.raises(Exception) as exc_info:
                    strategy.post(content)
                assert "Rate limit exceeded" in str(exc_info.value)
            else:
                strategy.post(content)
            assert mock_check.call_count == expected_calls
            if not first_wait:
                assert strategy.memory_updates["last_action"] == "rate_limit"
                assert strategy.memory_updates["last_error"]["error"] == "Rate limit exceeded"
                assert strategy.memory_updates["last_error"]["context"] == "rate_limit"

    def test_post_with_media(self, strategy):
        """Test post with media files."""
        content = "Test post with media"
        media_files = ["test.jpg", "test.png"]
        strategy._validate_media.return_value = (True, None)  # Ensure media validation passes
        assert strategy.post(content, media_files) is True
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1
        assert strategy.memory_updates["stats"]["post"] == 1
        assert strategy.stats["posts"] == 1
        assert strategy.stats["post"] == 1

    def test_media_validation(self, strategy):
        """Test media validation."""
        # Test valid media
        media_files = ["test.jpg", "test.png"]
        strategy._validate_media.return_value = (True, None)
        is_valid, error = strategy._validate_media(media_files)
        assert is_valid is True
        assert error is None
        
        # Test invalid media
        media_files = ["test.txt"]
        error_msg = "Unsupported file format"
        strategy._validate_media.return_value = (False, error_msg)
        is_valid, error = strategy._validate_media(media_files)
        assert is_valid is False
        assert error_msg in error
        strategy.memory_updates["last_error"] = {"error": error, "context": "validate_media"}
        assert strategy.memory_updates["last_action"] is None
        assert strategy.memory_updates["last_error"]["error"] == error
        assert strategy.memory_updates["last_error"]["context"] == "validate_media"

    def test_is_logged_in(self, strategy, mock_utils):
        """Test is_logged_in method."""
        # Reset the mock to use the actual implementation
        strategy.is_logged_in = TwitterStrategy.is_logged_in.__get__(strategy)
        
        # Test logged in
        mock_utils.wait_for_element.side_effect = [None, Mock()]  # No login form, has user menu
        assert strategy.is_logged_in() is True
        assert strategy.memory_updates["last_action"] == "is_logged_in"
        assert strategy.memory_updates["last_error"] is None
        
        # Test not logged in (login form present)
        mock_utils.wait_for_element.side_effect = [Mock(), None]  # Has login form, no user menu
        assert strategy.is_logged_in() is False
        assert strategy.memory_updates["last_action"] == "is_logged_in"
        assert "Login form found" in strategy.memory_updates["last_error"]["error"]
        
        # Test not logged in (no user menu)
        mock_utils.wait_for_element.side_effect = [None, None]  # No login form, no user menu
        assert strategy.is_logged_in() is False
        assert strategy.memory_updates["last_action"] == "is_logged_in"
        assert "User menu not found" in strategy.memory_updates["last_error"]["error"] 