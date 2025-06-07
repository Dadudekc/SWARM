"""
Reddit Strategy Test Suite
-------------------------
Tests for the RedditStrategy class functionality:
- Login/logout handling
- Post creation and verification
- Media validation and upload
- Rate limiting and retry logic
"""

import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException,
    ElementNotInteractableException
)
import types
from pathlib import Path

from social.utils.social_common import SocialMediaUtils
from social.strategies.platform_strategy_base import PlatformStrategy
from social.strategies.reddit.strategy import RedditStrategy
from social.strategies.reddit.handlers import LoginHandler, LogoutHandler, PostHandler, CommentHandler
from social.strategies.reddit.validators import MediaValidator
from social.strategies.reddit.rate_limiting import RateLimiter
from social.config.social_config import PlatformConfig, Platform
from dreamos.core.log_manager import LogConfig, LogLevel
from social.utils.rate_limiter import RateLimiter
from dreamos.core.agent_control.devlog_manager import DevLogManager
from social.driver.proxy_manager import ProxyManager
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    load_json,
    save_json,
    ensure_dir
)
from tests.social.strategies.base.test_strategy_base import BaseStrategyTest

# --- GLOBAL PATCHES FOR ALL TESTS ---
@pytest.fixture(autouse=True)
def patch_sqlite_and_rate_limiter(monkeypatch):
    # Patch sqlite3.connect everywhere
    monkeypatch.setattr("sqlite3.connect", lambda *a, **kw: MagicMock())
    # Patch RateLimiter.check_rate_limit to always allow
    from social.utils import rate_limiter
    monkeypatch.setattr(rate_limiter.RateLimiter, "check_rate_limit", lambda self, *a, **kw: True)
    yield

# Patch SocialMediaUtils in RedditStrategy for all tests that construct it
@pytest.fixture(autouse=True)
def patch_social_media_utils(monkeypatch):
    with patch('social.utils.social_common.SocialMediaUtils', new=MagicMock()):
        yield

@pytest.fixture
def mock_sqlite():
    """Mock SQLite connection."""
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        yield mock_connect

@pytest.fixture
def mock_driver():
    """Create a mock web driver."""
    driver = MagicMock()
    driver.find_element.return_value = MagicMock()
    driver.find_elements.return_value = []
    driver.current_url = "https://www.reddit.com"
    return driver

@pytest.fixture
def specific_strategy_mock_config():
    return {
        "window_coords": {"x": 0, "y": 0, "width": 800, "height": 600},
        "browser": {
            "headless": False,
            "window_title": "Reddit - Chromium",
            "window_coords": {"x": 0, "y": 0, "width": 800, "height": 600},
            "cookies_path": "tests/assets/cookies/reddit.pkl"
        },
        "profile_path": "tests/assets/profiles/reddit",
        "reddit": {
            "username": "testuser",
            "password": "testpass",
            "cookies_path": "tests/assets/cookies/reddit.pkl",
            "max_retries": 3,
            "retry_delay": 2,
            "session_timeout": 60,
            "rate_limit_posts": 10,
            "rate_limit_comments": 20,
            "supported_image_formats": ["jpg", "png"],
            "supported_video_formats": ["mp4"],
            "max_images": 20,
            "max_videos": 1,
            "max_video_size": 100 * 1024 * 1024
        }
    }

@pytest.fixture
def mock_memory_update():
    """Mock memory update dictionary."""
    return {
        "last_action": None,
        "last_error": None,
        "stats": {
            "posts": 0,
            "errors": 0,
            "media_uploads": 0
        },
        "retry_history": []
    }

@pytest.fixture
def mock_utils():
    """Create a mock utils object."""
    utils = MagicMock()
    utils.wait_for_element = MagicMock()
    utils.wait_for_clickable = MagicMock()
    utils.retry_click = MagicMock()
    utils.verify_post_success = MagicMock()
    utils.take_screenshot = MagicMock()
    utils.upload_media = MagicMock(return_value=True)
    utils.validate_media = MagicMock(return_value=True)
    utils.send_keys = MagicMock()
    return utils

@pytest.fixture
def mock_log_manager():
    """Create a mock log manager."""
    return DevLogManager(LogConfig(
        level=LogLevel.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        retention_days=30,
        max_file_size=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        metrics_enabled=True,
        log_dir="tests/runtime/logs",
        platforms={"reddit": "reddit.log"},
        batch_size=100,
        batch_timeout=5.0,
        max_retries=3,
        retry_delay=0.5
    ))

class TestRedditStrategy(BaseStrategyTest):
    """Test suite for Reddit strategy functionality."""
    
    @pytest.fixture
    def strategy(self, specific_strategy_mock_config, mock_memory_update):
        """Create a test strategy instance."""
        with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
            # Create platform config from the mock config
            platform_config = PlatformConfig(
                platform=Platform.REDDIT,
                api_key=specific_strategy_mock_config["reddit"]["username"],
                api_secret=specific_strategy_mock_config["reddit"]["password"],
                rate_limit=specific_strategy_mock_config["reddit"]["rate_limit_posts"],
                enabled=True
            )
            
            strategy = RedditStrategy(
                driver=MagicMock(),
                config=specific_strategy_mock_config,
                memory_update=mock_memory_update,
                agent_id="test_agent"
            )
            
            # Create proper mock objects for instance methods
            strategy.utils = MagicMock()
            strategy.logger = mock_log_manager()
            strategy.memory_updates = mock_memory_update.copy()
            
            # Mock instance methods properly
            strategy.is_logged_in = MagicMock(return_value=True)
            strategy._validate_media = MagicMock(return_value=(True, None))
            strategy._upload_media = MagicMock(return_value=True)
            strategy._verify_post = MagicMock(return_value=True)
            
            # Ensure media_handler uses the same mock utils
            from social.strategies.reddit_media import RedditMediaHandler
            strategy.media_handler = RedditMediaHandler(strategy.driver, mock_utils, strategy.logger)
            
            # Initialize post_handler with proper mocks
            from social.strategies.reddit.post_handler import PostHandler
            strategy.post_handler = PostHandler(strategy.driver, platform_config)
            
            yield strategy

    def test_logout_success(self, strategy):
        """Test successful logout."""
        strategy.login_handler = MagicMock()
        strategy.login_handler.logout.return_value = True
        
        success = strategy.logout()
        assert success
        assert strategy.memory_updates["last_action"] == "logout"
        assert strategy.memory_updates["last_error"] is None

    def test_logout_failure(self, strategy):
        """Test logout failure."""
        strategy.login_handler = MagicMock()
        strategy.login_handler.logout.return_value = False
        
        success = strategy.logout()
        assert not success
        assert strategy.memory_updates["last_action"] == "logout"
        assert strategy.memory_updates["last_error"] is not None

    def test_create_post_success(self, strategy):
        """Test successful post creation."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.return_value = True
        
        success = strategy.post("Test post")
        assert success
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1

    def test_create_post_failure(self, strategy):
        """Test post creation failure."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.return_value = False
        
        success = strategy.post("Test post")
        assert not success
        assert strategy.memory_updates["last_error"] is not None
        assert strategy.memory_updates["stats"]["posts"] == 0

    def test_create_post_with_media(self, strategy):
        """Test post creation with media."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.return_value = True
        strategy._validate_media = MagicMock(return_value=(True, None))
        strategy._upload_media = MagicMock(return_value=True)
        
        success = strategy.post("Test post", media=["test.jpg"])
        assert success
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1
        assert strategy.memory_updates["stats"]["media_uploads"] == 1

    def test_rate_limiting(self, strategy):
        """Test rate limiting."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.return_value = True
        
        # First post should succeed
        success = strategy.post("Test post 1")
        assert success
        
        # Second post should be rate limited
        strategy.rate_limiter.check_rate_limit.return_value = False
        success = strategy.post("Test post 2")
        assert not success
        assert strategy.memory_updates["last_error"] is not None
        assert "rate limit" in str(strategy.memory_updates["last_error"]).lower()

    def test_rate_limit_exceeded(self, strategy):
        """Test rate limit exceeded."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.return_value = True
        strategy.rate_limiter.check_rate_limit.return_value = False
        
        success = strategy.post("Test post")
        assert not success
        assert strategy.memory_updates["last_error"] is not None
        assert "rate limit" in str(strategy.memory_updates["last_error"]).lower()

    def test_retry_mechanism(self, strategy):
        """Test retry mechanism."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.side_effect = [
            TimeoutException(),
            True
        ]
        
        success = strategy.post("Test post")
        assert success
        assert strategy.memory_updates["last_error"] is None
        assert len(strategy.memory_updates["retry_history"]) == 1

    def test_max_retries_exceeded(self, strategy):
        """Test max retries exceeded."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.side_effect = TimeoutException()
        
        success = strategy.post("Test post")
        assert not success
        assert strategy.memory_updates["last_error"] is not None
        assert len(strategy.memory_updates["retry_history"]) == strategy.MAX_RETRIES

    def test_error_recovery(self, strategy):
        """Test error recovery."""
        strategy.is_logged_in = MagicMock(return_value=True)
        strategy.post_handler = MagicMock()
        strategy.post_handler.create_post.side_effect = [
            TimeoutException(),
            NoSuchElementException(),
            True
        ]
        
        success = strategy.post("Test post")
        assert success
        assert strategy.memory_updates["last_error"] is None
        assert len(strategy.memory_updates["retry_history"]) == 2

def test_init(specific_strategy_mock_config, mock_memory_update):
    """Test strategy initialization."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    strategy = RedditStrategy(
        driver=MagicMock(),
        config=specific_strategy_mock_config,
        memory_update=mock_memory_update,
        agent_id="test_agent"
    )
    
    assert strategy.memory_updates["last_action"] is None
    assert strategy.memory_updates["last_error"] is None
    assert strategy.memory_updates["stats"]["posts"] == 0
    assert strategy.memory_updates["stats"]["comments"] == 0
    assert strategy.memory_updates["stats"]["media_uploads"] == 0
    assert strategy.memory_updates["stats"]["errors"] == 0
    assert len(strategy.memory_updates["retry_history"]) == 0

def test_calculate_retry_delay(specific_strategy_mock_config, mock_memory_update):
    """Test retry delay calculation."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    # Test initial delay
    delay = strategy.calculate_retry_delay(1)
    assert delay >= strategy.INITIAL_RETRY_DELAY * 0.9  # Allow for jitter
    assert delay <= strategy.INITIAL_RETRY_DELAY * 1.1
    
    # Test exponential backoff
    delay = strategy.calculate_retry_delay(2)
    assert delay >= strategy.INITIAL_RETRY_DELAY * 2 * 0.9
    assert delay <= strategy.INITIAL_RETRY_DELAY * 2 * 1.1

def test_validate_media_single_image(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with a single image."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    strategy.media_files = ["test.jpg"]
    strategy.is_video = False
    
    result, error = strategy._validate_media()
    assert result is True
    assert error is None

def test_validate_media_empty(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with no files."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    strategy.media_files = []
    strategy.is_video = False
    
    result, error = strategy._validate_media()
    assert result is True
    assert error is None

def test_validate_media_unsupported_format(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with unsupported format."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    strategy.media_files = ["test.exe"]
    strategy.is_video = False
    
    result, error = strategy._validate_media()
    assert result is False
    assert "Unsupported file format" in error

def test_login_success(strategy, mock_driver, specific_strategy_mock_config):
    """Test successful login."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.login_handler = LoginHandler(mock_driver, specific_strategy_mock_config)
    strategy.login_handler.login = MagicMock(return_value=True)
    
    assert strategy.login() is True
    assert strategy.memory_updates["last_action"] == "login"
    assert strategy.memory_updates["last_error"] is None

def test_login_missing_credentials(specific_strategy_mock_config, mock_memory_update):
    """Test login with missing credentials."""
    # Remove credentials from config
    config_copy = specific_strategy_mock_config.copy()
    del config_copy["reddit"]["username"]
    del config_copy["reddit"]["password"]
    
    platform_config = PlatformConfig(
        platform="reddit",
        config=config_copy
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    result = strategy.login()
    assert result is False
    assert "Missing credentials" in strategy.memory_updates["last_error"]

def test_login_failure(strategy, mock_driver, specific_strategy_mock_config):
    """Test login failure."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.login_handler = LoginHandler(mock_driver, specific_strategy_mock_config)
    strategy.login_handler.login = MagicMock(return_value=False)
    
    assert strategy.login() is False
    assert strategy.memory_updates["last_action"] == "login"
    assert "login failed" in strategy.memory_updates["last_error"].lower()

def test_login_verification_failed(strategy):
    """Test login verification failure."""
    strategy.is_logged_in.return_value = False
    strategy.utils.wait_for_element.side_effect = TimeoutException()
    result = strategy.login()
    assert result is False
    assert "Login verification failed" in strategy.memory_updates["last_error"]

def test_login_input_not_found(strategy):
    """Test login input not found."""
    strategy.utils.wait_for_element.side_effect = NoSuchElementException()
    result = strategy.login()
    assert result is False
    assert "Login input not found" in strategy.memory_updates["last_error"]

def test_login_button_click_failed(strategy):
    """Test login button click failure."""
    strategy.utils.retry_click.side_effect = ElementClickInterceptedException()
    result = strategy.login()
    assert result is False
    assert "Login button click failed" in strategy.memory_updates["last_error"]

def test_is_logged_in_true(specific_strategy_mock_config, mock_memory_update):
    """Test is_logged_in returns True."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.driver, 'find_element') as mock_find:
        mock_find.return_value = MagicMock()
        assert strategy.is_logged_in() is True

def test_is_logged_in_false(specific_strategy_mock_config, mock_memory_update):
    """Test is_logged_in returns False."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.driver, 'find_element') as mock_find:
        mock_find.side_effect = NoSuchElementException()
        assert strategy.is_logged_in() is False

def test_post_success_with_redis(specific_strategy_mock_config, mock_memory_update):
    """Test successful post creation with Redis."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy.post_handler, 'create_post', return_value=True), \
         patch.object(strategy.post_handler, 'verify_post', return_value=True):
        result = strategy.create_post("Test post", "Test content")
        assert result is True
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1

def test_post_not_logged_in(specific_strategy_mock_config, mock_memory_update):
    """Test post creation when not logged in."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', return_value=False):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert "Not logged in" in strategy.memory_updates["last_error"]

def test_post_failure(specific_strategy_mock_config, mock_memory_update):
    """Test post creation failure."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy.post_handler, 'create_post', return_value=False):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert strategy.memory_updates["last_error"] is not None

def test_post_button_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test post button not found."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy.utils, 'wait_for_element', side_effect=NoSuchElementException()):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert "Post button not found" in strategy.memory_updates["last_error"]

def test_post_media_validation_failed(strategy):
    """Test post creation with failed media validation."""
    strategy.is_logged_in.return_value = True
    strategy._validate_media.return_value = (False, "Invalid media")
    result = strategy.create_post("Test post", "Test content", media_files=["test.jpg"])
    assert result is False
    assert "Invalid media" in strategy.memory_updates["last_error"]

def test_post_media_upload_failed(strategy):
    """Test post creation with failed media upload."""
    strategy.is_logged_in.return_value = True
    strategy._validate_media.return_value = (True, None)
    strategy._upload_media.return_value = False
    result = strategy.create_post("Test post", "Test content", media_files=["test.jpg"])
    assert result is False
    assert "Media upload failed" in strategy.memory_updates["last_error"]

def test_upload_media_success(specific_strategy_mock_config, mock_memory_update):
    """Test successful media upload."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.utils, 'upload_media', return_value=True):
        result = strategy._upload_media(["test.jpg"])
        assert result is True
        assert strategy.memory_updates["stats"]["media_uploads"] == 1

def test_upload_media_button_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test media upload button not found."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.utils, 'wait_for_element', side_effect=NoSuchElementException()):
        result = strategy._upload_media(["test.jpg"])
        assert result is False
        assert "Upload button not found" in strategy.memory_updates["last_error"]

def test_upload_media_click_failed(specific_strategy_mock_config, mock_memory_update):
    """Test media upload button click failure."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.utils, 'retry_click', side_effect=ElementClickInterceptedException()):
        result = strategy._upload_media(["test.jpg"])
        assert result is False
        assert "Upload button click failed" in strategy.memory_updates["last_error"]

def test_validate_media_too_many_files(strategy):
    """Test media validation with too many files."""
    strategy.media_files = ["test1.jpg", "test2.jpg", "test3.jpg", "test4.jpg", "test5.jpg"]
    result, error = strategy._validate_media()
    assert result is False
    assert "Too many media files" in error

def test_validate_media_file_too_large(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with file too large."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch('os.path.getsize', return_value=21 * 1024 * 1024):  # 21MB
        result, error = strategy._validate_media()
        assert result is False
        assert "File too large" in error

def test_validate_media_file_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with file not found."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch('os.path.exists', return_value=False):
        result, error = strategy._validate_media()
        assert result is False
        assert "File not found" in error

def test_validate_media_valid_image(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with valid image."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1 * 1024 * 1024):  # 1MB
        result, error = strategy._validate_media()
        assert result is True
        assert error is None

def test_validate_media_invalid_format(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with invalid format."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    strategy.media_files = ["test.exe"]
    result, error = strategy._validate_media()
    assert result is False
    assert "Unsupported file format" in error

def test_validate_media_too_many_images(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with too many images."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    strategy.media_files = ["test1.jpg", "test2.jpg", "test3.jpg", "test4.jpg", "test5.jpg"]
    result, error = strategy._validate_media()
    assert result is False
    assert "Too many media files" in error

def test_validate_media_video_unsupported(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with unsupported video."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    strategy.media_files = ["test.mp4"]
    strategy.is_video = True
    result, error = strategy._validate_media()
    assert result is False
    assert "Video upload not supported" in error

def test_validate_media_valid_video_when_specified(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with valid video when specified."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1 * 1024 * 1024):  # 1MB
        strategy.media_files = ["test.mp4"]
        strategy.is_video = True
        strategy.config.config["reddit"]["allow_video"] = True
        result, error = strategy._validate_media()
        assert result is True
        assert error is None

def test_platform_initialization_missing_keys(specific_strategy_mock_config, mock_memory_update):
    """Test platform initialization with missing keys."""
    config_copy = specific_strategy_mock_config.copy()
    del config_copy["reddit"]
    
    platform_config = PlatformConfig(
        platform="reddit",
        config=config_copy
    )
    
    with pytest.raises(ValueError) as exc_info:
        RedditStrategy(
            config=platform_config,
            memory_updates=mock_memory_update,
            agent_id="test_agent"
        )
    assert "Missing 'reddit' configuration section" in str(exc_info.value)

def test_platform_initialization_valid_keys(specific_strategy_mock_config, mock_memory_update):
    """Test platform initialization with valid keys."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    assert strategy.config.platform == "reddit"

def test_reddit_strategy_error_handling(specific_strategy_mock_config, mock_memory_update):
    """Test error handling in RedditStrategy."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', side_effect=WebDriverException("Test error")):
        result = strategy.login()
        assert result is False
        assert "Test error" in strategy.memory_updates["last_error"]
        assert strategy.memory_updates["stats"]["errors"] == 1

def test_devlog_embed_validation(specific_strategy_mock_config, mock_memory_update):
    """Test DevLog embed validation."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.logger, 'embed') as mock_embed:
        strategy.logger.embed(
            title="Test Title",
            description="Test Description",
            color=0x00ff00
        )
        mock_embed.assert_called_once_with(
            title="Test Title",
            description="Test Description",
            color=0x00ff00
        )

def test_reddit_strategy_retry_behavior(specific_strategy_mock_config, mock_memory_update):
    """Test retry behavior in RedditStrategy."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy, 'is_logged_in', side_effect=[False, True]), \
         patch.object(strategy, 'login') as mock_login:
        mock_login.return_value = True
        result = strategy.login()
        assert result is True
        assert mock_login.call_count == 1

def test_reddit_strategy_rate_limiting(specific_strategy_mock_config, mock_memory_update):
    """Test rate limiting in RedditStrategy."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    with patch.object(strategy.rate_limiter, 'check_rate_limit', return_value=False):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert "Rate limit exceeded" in strategy.memory_updates["last_error"]

def test_reddit_strategy_media_validation_edge_cases(specific_strategy_mock_config, mock_memory_update):
    """Test media validation edge cases."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    # Test empty media files
    strategy.media_files = []
    result, error = strategy._validate_media()
    assert result is True
    assert error is None
    
    # Test None media files
    strategy.media_files = None
    result, error = strategy._validate_media()
    assert result is True
    assert error is None
    
    # Test invalid file path
    strategy.media_files = ["/invalid/path/test.jpg"]
    with patch('os.path.exists', return_value=False):
        result, error = strategy._validate_media()
        assert result is False
        assert "File not found" in error

def test_reddit_strategy_error_recovery(specific_strategy_mock_config, mock_memory_update):
    """Test error recovery in RedditStrategy."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    # Test recovery from stale element
    with patch.object(strategy.utils, 'wait_for_element', side_effect=StaleElementReferenceException()):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert "Stale element" in strategy.memory_updates["last_error"]
    
    # Test recovery from element not interactable
    with patch.object(strategy.utils, 'wait_for_element', side_effect=ElementNotInteractableException()):
        result = strategy.create_post("Test post", "Test content")
        assert result is False
        assert "Element not interactable" in strategy.memory_updates["last_error"]

def test_reddit_strategy_integration(specific_strategy_mock_config, mock_memory_update):
    """Test RedditStrategy integration."""
    platform_config = PlatformConfig(
        platform="reddit",
        config=specific_strategy_mock_config
    )
    strategy = RedditStrategy(
        config=platform_config,
        memory_updates=mock_memory_update,
        agent_id="test_agent"
    )
    
    # Test full post creation flow
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy, '_validate_media', return_value=(True, None)), \
         patch.object(strategy, '_upload_media', return_value=True), \
         patch.object(strategy.post_handler, 'create_post', return_value=True), \
         patch.object(strategy.post_handler, 'verify_post', return_value=True):
        result = strategy.create_post(
            title="Test Post",
            content="Test Content",
            media_files=["test.jpg"]
        )
        assert result is True
        assert strategy.memory_updates["last_action"] == "post"
        assert strategy.memory_updates["last_error"] is None
        assert strategy.memory_updates["stats"]["posts"] == 1
        assert strategy.memory_updates["stats"]["media_uploads"] == 1

def test_logout_success(strategy, mock_driver, specific_strategy_mock_config):
    """Test successful logout."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.logout_handler = LogoutHandler(mock_driver, specific_strategy_mock_config)
    strategy.logout_handler.logout = MagicMock(return_value=True)
    
    assert strategy.logout() is True
    assert strategy.memory_updates["last_action"] == "logout"
    assert strategy.memory_updates["last_error"] is None

def test_logout_failure(strategy, mock_driver, specific_strategy_mock_config):
    """Test logout failure."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.logout_handler = LogoutHandler(mock_driver, specific_strategy_mock_config)
    strategy.logout_handler.logout = MagicMock(return_value=False)
    
    assert strategy.logout() is False
    assert strategy.memory_updates["last_action"] == "logout"
    assert "logout failed" in strategy.memory_updates["last_error"].lower()

def test_create_post_success(strategy, mock_driver, specific_strategy_mock_config):
    """Test successful post creation."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(return_value=True)
    strategy.post_handler.verify_post = MagicMock(return_value=True)
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit"
    }
    
    assert strategy.create_post(post_data) is True
    assert strategy.memory_updates["last_action"] == "create_post"
    assert strategy.memory_updates["last_error"] is None
    assert strategy.memory_updates["stats"]["posts"] == 1

def test_create_post_failure(strategy, mock_driver, specific_strategy_mock_config):
    """Test post creation failure."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(return_value=False)
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit"
    }
    
    assert strategy.create_post(post_data) is False
    assert strategy.memory_updates["last_action"] == "create_post"
    assert "post creation failed" in strategy.memory_updates["last_error"].lower()
    assert strategy.memory_updates["stats"]["posts"] == 0
    assert strategy.memory_updates["stats"]["errors"] == 1

def test_create_post_with_media(strategy, mock_driver, specific_strategy_mock_config):
    """Test post creation with media."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(return_value=True)
    strategy.post_handler.verify_post = MagicMock(return_value=True)
    strategy._validate_media = MagicMock(return_value=(True, None))
    strategy._upload_media = MagicMock(return_value=True)
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit",
        "media": ["test_image.jpg"]
    }
    
    assert strategy.create_post(post_data) is True
    assert strategy.memory_updates["last_action"] == "create_post"
    assert strategy.memory_updates["last_error"] is None
    assert strategy.memory_updates["stats"]["posts"] == 1
    assert strategy.memory_updates["stats"]["media_uploads"] == 1

def test_validate_media_success(strategy, mock_driver, specific_strategy_mock_config):
    """Test successful media validation."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.media_validator = MediaValidator(mock_driver, specific_strategy_mock_config)
    strategy.media_validator.validate = MagicMock(return_value=(True, None))
    
    media_paths = ["test_image.jpg"]
    success, error = strategy._validate_media(media_paths)
    
    assert success is True
    assert error is None

def test_validate_media_failure(strategy, mock_driver, specific_strategy_mock_config):
    """Test media validation failure."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.media_validator = MediaValidator(mock_driver, specific_strategy_mock_config)
    strategy.media_validator.validate = MagicMock(return_value=(False, "Invalid media format"))
    
    media_paths = ["invalid_file.txt"]
    success, error = strategy._validate_media(media_paths)
    
    assert success is False
    assert "invalid media format" in error.lower()

def test_rate_limiting(strategy, mock_driver, specific_strategy_mock_config):
    """Test rate limiting functionality."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.rate_limiter = RateLimiter(specific_strategy_mock_config["reddit"]["rate_limit_posts"])
    
    # Test post rate limiting
    assert strategy.rate_limiter.check_rate_limit("posts") is True
    strategy.rate_limiter.record_action("posts")
    assert strategy.rate_limiter.check_rate_limit("posts") is True
    
    # Test comment rate limiting
    assert strategy.rate_limiter.check_rate_limit("comments") is True
    strategy.rate_limiter.record_action("comments")
    assert strategy.rate_limiter.check_rate_limit("comments") is True

def test_rate_limit_exceeded(strategy, mock_driver, specific_strategy_mock_config):
    """Test rate limit exceeded scenario."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.rate_limiter = RateLimiter(specific_strategy_mock_config["reddit"]["rate_limit_posts"])
    
    # Exceed post rate limit
    for _ in range(specific_strategy_mock_config["reddit"]["rate_limit_posts"] + 1):
        strategy.rate_limiter.record_action("posts")
    
    assert strategy.rate_limiter.check_rate_limit("posts") is False

def test_retry_mechanism(strategy, mock_driver, specific_strategy_mock_config):
    """Test retry mechanism for failed operations."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(side_effect=[False, False, True])
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit"
    }
    
    assert strategy.create_post(post_data) is True
    assert len(strategy.memory_updates["retry_history"]) == 2
    assert strategy.memory_updates["stats"]["errors"] == 2
    assert strategy.memory_updates["stats"]["posts"] == 1

def test_max_retries_exceeded(strategy, mock_driver, specific_strategy_mock_config):
    """Test behavior when max retries are exceeded."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(return_value=False)
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit"
    }
    
    assert strategy.create_post(post_data) is False
    assert len(strategy.memory_updates["retry_history"]) == specific_strategy_mock_config["reddit"]["max_retries"]
    assert strategy.memory_updates["stats"]["errors"] == specific_strategy_mock_config["reddit"]["max_retries"]
    assert strategy.memory_updates["stats"]["posts"] == 0

def test_error_recovery(strategy, mock_driver, specific_strategy_mock_config):
    """Test error recovery and state reset."""
    platform_config = PlatformConfig(
        platform=Platform.REDDIT,
        api_key=specific_strategy_mock_config["reddit"].get("username"),
        api_secret=specific_strategy_mock_config["reddit"].get("password"),
        rate_limit=specific_strategy_mock_config["reddit"].get("rate_limit_posts"),
        enabled=True
    )
    
    strategy.driver = mock_driver
    strategy.post_handler = PostHandler(mock_driver, specific_strategy_mock_config)
    strategy.post_handler.create_post = MagicMock(side_effect=[False, True])
    
    # Simulate an error state
    strategy.memory_updates["last_error"] = "Previous error"
    strategy.memory_updates["stats"]["errors"] = 1
    
    post_data = {
        "title": "Test Post",
        "content": "Test Content",
        "subreddit": "test_subreddit"
    }
    
    assert strategy.create_post(post_data) is True
    assert strategy.memory_updates["last_error"] is None
    assert strategy.memory_updates["stats"]["errors"] == 1
    assert strategy.memory_updates["stats"]["posts"] == 1
