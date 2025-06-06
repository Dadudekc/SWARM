import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import TimeoutException, WebDriverException, ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By
from datetime import datetime

from dreamos.social.utils.social_common import SocialMediaUtils
from social.strategies.platform_strategy_base import PlatformStrategy
from social.strategies.reddit.strategy import RedditStrategy
from social.strategies.reddit.handlers import LoginHandler, LogoutHandler, PostHandler, CommentHandler
from social.strategies.reddit.validators import MediaValidator
from social.strategies.reddit.rate_limiting import RateLimiter
from social.config.social_config import PlatformConfig
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.social.utils import rate_limiter
from dreamos.core.agent_control.devlog_manager import DevLogManager
from social.driver.proxy_manager import ProxyManager

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
    """Fixture for Reddit strategy configuration. Ensures required keys for all tests."""
    config = {
        "browser": {
            "headless": False,
            "window_title": "Reddit - Chromium",
            "window_coords": {"x": 0, "y": 0, "width": 1920, "height": 1080},
            "cookies_path": "tests/assets/cookies/reddit.pkl",
            "profile_path": "tests/assets/profiles/reddit"
        },
        "reddit": {
            "username": "test_user",
            "password": "test_pass",
            "timeout": 10,
            "retry_attempts": 3,
            "rate_limit": {
                "posts_per_hour": 10,
                "comments_per_hour": 20
            }
        },
        "log_config": LogConfig(
            log_dir="tests/runtime/logs",
            level=LogLevel.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            retention_days=30,
            max_file_size=10 * 1024 * 1024,
            backup_count=5,
            metrics_enabled=True,
            platforms={"reddit": "reddit.log"},
            batch_size=100,
            batch_timeout=5,
            max_retries=2,
            retry_delay=0.1
        )
    }
    # Guarantee required keys for all downstream code/tests
    if "cookies_path" not in config["browser"]:
        config["browser"]["cookies_path"] = "tests/assets/cookies/reddit.pkl"
    if "profile_path" not in config["browser"]:
        config["browser"]["profile_path"] = "tests/assets/profiles/reddit"
    if "reddit" not in config:
        config["reddit"] = {}
    return config

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
    return MagicMock()

@pytest.fixture
def strategy(specific_strategy_mock_config, mock_memory_update):
    """Create a test strategy instance."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update, "test_agent")
        
        # Create proper mock objects for instance methods
        strategy.utils = MagicMock()
        strategy.logger = MagicMock()
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
        strategy.post_handler = PostHandler(strategy.driver, specific_strategy_mock_config)
        strategy.post_handler.create_post = MagicMock(return_value=True)
        strategy.post_handler.verify_post = MagicMock(return_value=True)
        
        return strategy

def test_init(specific_strategy_mock_config, mock_memory_update):
    """Test strategy initialization."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    assert strategy.memory_updates["last_action"] is None
    assert strategy.memory_updates["last_error"] is None
    assert strategy.memory_updates["stats"]["posts"] == 0
    assert strategy.memory_updates["stats"]["comments"] == 0
    assert strategy.memory_updates["stats"]["media_uploads"] == 0
    assert strategy.memory_updates["stats"]["errors"] == 0
    assert len(strategy.memory_updates["retry_history"]) == 0

def test_calculate_retry_delay(specific_strategy_mock_config, mock_memory_update):
    """Test retry delay calculation."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Test initial delay
    delay = strategy.calculate_retry_delay(1)
    assert delay >= strategy.INITIAL_RETRY_DELAY * 0.9  # Allow for jitter
    assert delay <= strategy.INITIAL_RETRY_DELAY * 1.1
    
    # Test exponential backoff
    delay = strategy.calculate_retry_delay(2)
    assert delay >= strategy.INITIAL_RETRY_DELAY * 2 * 0.9
    assert delay <= strategy.INITIAL_RETRY_DELAY * 2 * 1.1
    
    # Test max delay cap
    delay = strategy.calculate_retry_delay(10)
    assert delay <= strategy.MAX_RETRY_DELAY * 1.1  # Allow for jitter

def test_validate_media_single_image(specific_strategy_mock_config, mock_memory_update):
    """Test validating a single image file."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.is_logged_in = MagicMock(return_value=True)
    strategy.utils = MagicMock()
    
    # Test with valid image
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.jpg')):
        is_valid, error = strategy._validate_media(['test.jpg'], is_video=False)
        assert is_valid
        assert error is None
        
    # Test with invalid format
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.txt')):
        is_valid, error = strategy._validate_media(['test.txt'], is_video=False)
        assert not is_valid
        assert error is not None

def test_validate_media_empty(specific_strategy_mock_config, mock_memory_update):
    """Test validating empty media list."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    is_valid, error = strategy._validate_media([], is_video=False)
    assert is_valid
    assert error is None

def test_validate_media_unsupported_format(specific_strategy_mock_config, mock_memory_update):
    """Test validating unsupported media format."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.xyz')):
        is_valid, error = strategy._validate_media(['test.xyz'], is_video=False)
        assert not is_valid
        assert error is not None

def test_login_success(specific_strategy_mock_config, mock_memory_update):
    """Test successful login."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock login handler
    strategy.login_handler = MagicMock()
    strategy.login_handler.login.return_value = True
    
    success = strategy.login()
    assert success
    assert strategy.memory_updates["last_action"] == "login"
    assert strategy.memory_updates["stats"]["login"] == 1
    assert strategy.memory_updates["last_error"] is None

def test_login_missing_credentials(specific_strategy_mock_config, mock_memory_update):
    """Test login with missing credentials."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Remove credentials
    strategy.credentials = {}
    
    success = strategy.login()
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Missing credentials" in str(strategy.memory_updates["last_error"]["error"])

def test_login_failure(strategy):
    """Test login failure."""
    # Mock login handler to fail
    strategy.login_handler.login.return_value = False
    
    success = strategy.login()
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Login failed" in str(strategy.memory_updates["last_error"]["error"])

def test_login_verification_failed(strategy):
    """Test login verification failure."""
    # Mock login handler to succeed but verification to fail
    strategy.login_handler.login.return_value = True
    strategy.is_logged_in.return_value = False
    
    success = strategy.login()
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_login_input_not_found(strategy):
    """Test login with missing input fields."""
    # Mock login handler to raise NoSuchElementException
    strategy.login_handler.login.side_effect = NoSuchElementException("Login input not found")
    
    success = strategy.login()
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_login_button_click_failed(strategy):
    """Test login button click failure."""
    # Mock login handler to raise ElementClickInterceptedException
    strategy.login_handler.login.side_effect = ElementClickInterceptedException("Click intercepted")
    
    success = strategy.login()
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_is_logged_in_true(specific_strategy_mock_config, mock_memory_update):
    """Test is_logged_in when user is logged in."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock utils to return None for login form and a mock for user menu
    strategy.utils.wait_for_element.side_effect = [None, MagicMock()]
    
    assert strategy.is_logged_in()
    assert strategy.memory_updates["last_action"] == "is_logged_in"
    assert strategy.memory_updates["last_error"] is None

def test_is_logged_in_false(specific_strategy_mock_config, mock_memory_update):
    """Test is_logged_in when user is not logged in."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock utils to return a mock for login form and None for user menu
    strategy.utils.wait_for_element.side_effect = [MagicMock(), None]
    
    assert not strategy.is_logged_in()
    assert strategy.memory_updates["last_action"] == "is_logged_in"
    assert strategy.memory_updates["last_error"] is not None

def test_post_success_with_redis(specific_strategy_mock_config, mock_memory_update):
    """Test successful post with Redis."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.is_logged_in = MagicMock(return_value=True)
    strategy._check_rate_limit = MagicMock(return_value=True)
    strategy.create_post = MagicMock(return_value=True)
    strategy._verify_post_success = MagicMock(return_value=True)
    
    success = strategy.post("Test content", title="Test title")
    assert success
    assert strategy.memory_updates["last_action"] == "post"
    assert strategy.memory_updates["stats"]["posts"] == 1
    assert strategy.memory_updates["last_error"] is None

def test_post_not_logged_in(specific_strategy_mock_config, mock_memory_update):
    """Test post when not logged in."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock is_logged_in to return False
    strategy.is_logged_in = MagicMock(return_value=False)
    
    success = strategy.post("Test content")
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Not logged in" in str(strategy.memory_updates["last_error"]["error"])

def test_post_failure(specific_strategy_mock_config, mock_memory_update):
    """Test post failure."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.is_logged_in = MagicMock(return_value=True)
    strategy._check_rate_limit = MagicMock(return_value=True)
    strategy.create_post = MagicMock(return_value=False)
    
    success = strategy.post("Test content")
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Post verification failed" in str(strategy.memory_updates["last_error"]["error"])

def test_post_button_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test post button not found."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.is_logged_in = MagicMock(return_value=True)
    strategy._check_rate_limit = MagicMock(return_value=True)
    strategy.create_post = MagicMock(side_effect=NoSuchElementException("Post button not found"))
    
    success = strategy.post("Test content")
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_post_media_validation_failed(strategy):
    """Test post with invalid media."""
    # Mock validate_media to fail
    strategy._validate_media = MagicMock(return_value=(False, "Invalid media"))
    
    success = strategy.create_post("Test title", "Test content", ["invalid.jpg"])
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_post_media_upload_failed(strategy):
    """Test post with media upload failure."""
    # Mock validate_media to succeed but upload to fail
    strategy._validate_media = MagicMock(return_value=(True, None))
    strategy._upload_media = MagicMock(return_value=False)
    
    success = strategy.create_post("Test title", "Test content", ["test.jpg"])
    assert not success
    assert strategy.memory_updates["last_error"] is not None

def test_upload_media_success(specific_strategy_mock_config, mock_memory_update):
    """Test successful media upload."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy._validate_media = MagicMock(return_value=(True, None))
    strategy._upload_media = MagicMock(return_value=True)
    
    success = strategy._upload_media(["test.jpg"])
    assert success
    assert strategy.memory_updates["last_action"] == "media_upload"
    assert strategy.memory_updates["stats"]["media_uploads"] == 1

def test_upload_media_button_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test media upload with missing button."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock utils to return None for upload button
    strategy.utils.wait_for_element.return_value = None
    
    success = strategy._upload_media(["test.jpg"])
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Media upload button not found" in str(strategy.memory_updates["last_error"]["error"])

def test_upload_media_click_failed(specific_strategy_mock_config, mock_memory_update):
    """Test media upload with click failure."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock utils to raise ElementClickInterceptedException
    strategy.utils.wait_for_element.return_value = MagicMock()
    strategy.utils.wait_for_element.return_value.click.side_effect = ElementClickInterceptedException("Click intercepted")
    
    success = strategy._upload_media(["test.jpg"])
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Click intercepted" in str(strategy.memory_updates["last_error"]["error"])

def test_validate_media_too_many_files(strategy):
    """Test media validation with too many files."""
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.jpg')):
        is_valid, error = strategy._validate_media(['test1.jpg', 'test2.jpg', 'test3.jpg'], is_video=True)
        assert not is_valid
        assert "Too many files" in error

def test_validate_media_file_too_large(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with file too large."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=200 * 1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.jpg')):
        is_valid, error = strategy._validate_media(['test.jpg'])
        assert not is_valid
        assert "File too large" in error

def test_validate_media_file_not_found(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with missing file."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=False):
        is_valid, error = strategy._validate_media(['test.jpg'])
        assert not is_valid
        assert "File not found" in error

def test_validate_media_valid_image(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with valid image."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.jpg')):
        is_valid, error = strategy._validate_media(['test.jpg'])
        assert is_valid
        assert error is None

def test_validate_media_invalid_format(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with invalid format."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.xyz')):
        is_valid, error = strategy._validate_media(['test.xyz'])
        assert not is_valid
        assert "Unsupported file format" in error

def test_validate_media_too_many_images(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with too many images."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Create list of too many image files
    files = [f'test{i}.jpg' for i in range(21)]  # MAX_IMAGES + 1
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.jpg')):
        is_valid, error = strategy._validate_media(files)
        assert not is_valid
        assert "Too many files" in error

def test_validate_media_video_unsupported(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with unsupported video format."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.xyz')):
        is_valid, error = strategy._validate_media(['test.xyz'], is_video=True)
        assert not is_valid
        assert "Unsupported file format" in error

def test_validate_media_valid_video_when_specified(specific_strategy_mock_config, mock_memory_update):
    """Test media validation with valid video when specified."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock file operations
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=1024 * 1024), \
         patch('os.path.splitext', return_value=('test', '.mp4')):
        is_valid, error = strategy._validate_media(['test.mp4'], is_video=True)
        assert is_valid
        assert error is None

def test_platform_initialization_missing_keys(specific_strategy_mock_config, mock_memory_update):
    """Test platform initialization with missing keys."""
    # Remove required keys
    del specific_strategy_mock_config['browser']['window_title']
    
    with pytest.raises(ValueError) as exc_info:
        RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    assert "Missing required browser configuration keys" in str(exc_info.value)

def test_platform_initialization_valid_keys(specific_strategy_mock_config, mock_memory_update):
    """Test platform initialization with valid keys."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    assert strategy.config == specific_strategy_mock_config
    assert strategy.memory_updates == mock_memory_update

def test_reddit_strategy_error_handling(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy error handling."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Test error handling
    strategy._handle_error("Test error", "test_action")
    assert strategy.memory_updates["last_error"] is not None
    assert strategy.memory_updates["last_action"] == "test_action"
    assert "Test error" in str(strategy.memory_updates["last_error"]["error"])

def test_devlog_embed_validation(specific_strategy_mock_config, mock_memory_update):
    """Test devlog embed validation."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.create_post = MagicMock(return_value=True)
    
    success = strategy.post_devlog("Test title", "Test content")
    assert success
    assert strategy.memory_updates["last_action"] == "post"
    assert strategy.memory_updates["stats"]["post"] == 1
    assert strategy.memory_updates["stats"]["devlogs"] == 1

def test_reddit_strategy_retry_behavior(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy retry behavior."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.create_post = MagicMock(side_effect=[False, True])  # Fail first, succeed second
    
    success = strategy.retry_operation("post", max_retries=2)
    assert success
    assert len(strategy.memory_updates["retry_history"]) == 1

def test_reddit_strategy_rate_limiting(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy rate limiting."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock rate limiter
    strategy._check_rate_limit = MagicMock(return_value=False)
    
    success = strategy.post("Test content")
    assert not success
    assert strategy.memory_updates["last_error"] is not None
    assert "Rate limit exceeded" in str(strategy.memory_updates["last_error"]["error"])

def test_reddit_strategy_media_validation_edge_cases(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy media validation edge cases."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Test empty list
    is_valid, error = strategy._validate_media([])
    assert is_valid
    assert error is None
    
    # Test None
    is_valid, error = strategy._validate_media(None)
    assert is_valid
    assert error is None
    
    # Test invalid file path
    is_valid, error = strategy._validate_media(["/invalid/path/file.jpg"])
    assert not is_valid
    assert "File not found" in error

def test_reddit_strategy_error_recovery(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy error recovery."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.create_post = MagicMock(side_effect=[Exception("Test error"), True])
    
    success = strategy.retry_operation("post", max_retries=2)
    assert success
    assert len(strategy.memory_updates["retry_history"]) == 1

def test_reddit_strategy_integration(specific_strategy_mock_config, mock_memory_update):
    """Test Reddit strategy integration."""
    strategy = RedditStrategy(specific_strategy_mock_config, mock_memory_update)
    
    # Mock necessary methods
    strategy.is_logged_in = MagicMock(return_value=True)
    strategy._check_rate_limit = MagicMock(return_value=True)
    strategy.create_post = MagicMock(return_value=True)
    strategy._verify_post_success = MagicMock(return_value=True)
    
    # Test full post flow
    success = strategy.post("Test content", title="Test title")
    assert success
    assert strategy.memory_updates["last_action"] == "post"
    assert strategy.memory_updates["stats"]["posts"] == 1
    assert strategy.memory_updates["last_error"] is None 