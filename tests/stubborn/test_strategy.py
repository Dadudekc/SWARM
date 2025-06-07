"""
Test Reddit Strategy
------------------
Tests for Reddit posting and interaction functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from social.strategies.reddit.strategy import RedditStrategy
from dreamos.core.log_manager import LogManager
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir
)

@pytest.fixture
def mock_driver():
    driver = Mock()
    driver.current_url = "https://www.reddit.com"
    return driver

@pytest.fixture
def mock_config():
    """Create mock configuration. Ensures required keys for all tests."""
    config = {
        "reddit": {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "username": "test_username",
            "password": "test_password",
            "user_agent": "test_user_agent",
            "subreddits": ["test_subreddit"],
            "max_posts_per_day": 10,
            "max_comments_per_day": 20,
            "post_delay": 3600,
            "comment_delay": 1800
        },
        "browser": {
            "headless": True,
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "user_agent": "test_user_agent",
            "proxy": None,
            "window_size": {
                "width": 1920,
                "height": 1080
            },
            "window_title": "Test Browser Window",
            "window_coords": {
                "x": 0,
                "y": 0
            },
            "cookies_path": "tests/data/cookies",
            "profile_path": "tests/data/profile",
            "download_path": "tests/data/downloads",
            "temp_path": "tests/data/temp"
        },
        "log_config": LogConfig(
            level=LogLevel.INFO,
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            retention_days=7,
            max_file_size=10 * 1024 * 1024,
            backup_count=5,
            metrics_enabled=True,
            log_dir="logs",
            platforms={"reddit": "reddit.log"},
            batch_size=100,
            batch_timeout=1.0,
            max_retries=3,
            retry_delay=0.5
        ),
        "window_title": "Test Browser Window",
        "window_coords": {
            "x": 0,
            "y": 0,
            "width": 1920,
            "height": 1080
        }
    }
    # Guarantee required keys for all downstream code/tests
    # Add cookies_path/profile_path to reddit section as well if needed
    config["reddit"]["cookies_path"] = config["browser"]["cookies_path"]
    config["reddit"]["profile_path"] = config["browser"]["profile_path"]
    return config

@pytest.fixture
def mock_memory_update():
    return {
        "last_error": None,
        "stats": {"login": 0, "post": 0, "comment": 0},
        "last_action": None,
        "retry_history": [],
        "operation_times": {}
    }

@pytest.fixture
def strategy(mock_driver, mock_config, mock_memory_update):
    """Create a RedditStrategy instance for testing."""
    with patch('social.strategies.reddit.strategy.PostHandler') as mock_post_handler, \
         patch('social.strategies.reddit.strategy.CommentHandler') as mock_comment_handler, \
         patch('social.strategies.reddit.strategy.LoginHandler') as mock_login_handler:
        
        # Create a real LogManager instance
        log_manager = LogManager(LogConfig(
            level=LogLevel.DEBUG,
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            retention_days=7,
            max_file_size=10 * 1024 * 1024,
            backup_count=5,
            metrics_enabled=True,
            log_dir="tests/runtime/logs",
            platforms={"reddit": "reddit.log"},
            batch_size=100,
            batch_timeout=1.0,
            max_retries=3,
            retry_delay=0.5
        ))
        
        mock_post_handler.return_value = MagicMock()
        mock_comment_handler.return_value = MagicMock()
        mock_login_handler.return_value.is_logged_in.return_value = True
        mock_login_handler.return_value.login.return_value = True
        
        strategy = RedditStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.logger = log_manager
        strategy.post_handler = mock_post_handler.return_value
        strategy.comment_handler = mock_comment_handler.return_value
        strategy.login_handler = mock_login_handler.return_value
        
        return strategy

def test_initialization(strategy, mock_config):
    """Test strategy initialization."""
    assert strategy.username == mock_config["reddit"]["username"]
    assert strategy.password == mock_config["reddit"]["password"]
    assert strategy.client_id == mock_config["reddit"]["client_id"]
    assert strategy.client_secret == mock_config["reddit"]["client_secret"]
    assert strategy.user_agent == mock_config["reddit"]["user_agent"]

def test_login(strategy):
    """Test login functionality."""
    with patch.object(strategy, '_perform_login') as mock_login:
        mock_login.return_value = True
        assert strategy.login() is True
        mock_login.assert_called_once()

def test_post_success(strategy):
    """Test successful post creation."""
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy, 'post_handler') as mock_handler:
        mock_handler.create_post.return_value = True
        assert strategy.post("Test Content", title="Test Title") is True
        mock_handler.create_post.assert_called_once_with("Test Title", "Test Content", [])

def test_post_not_logged_in(strategy):
    """Test post attempt when not logged in."""
    with patch.object(strategy, 'is_logged_in', return_value=False):
        with pytest.raises(Exception) as exc_info:
            strategy.post("Test Content")
        assert str(exc_info.value) == "Not logged in"

def test_comment_success(strategy):
    """Test successful comment creation."""
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy, 'comment_handler') as mock_handler:
        mock_handler.create_comment.return_value = True
        assert strategy.comment("Test Comment", "post_id") is True
        mock_handler.create_comment.assert_called_once_with("post_id", "Test Comment")

def test_comment_not_logged_in(strategy):
    """Test comment attempt when not logged in."""
    with patch.object(strategy, 'is_logged_in', return_value=False):
        with pytest.raises(Exception) as exc_info:
            strategy.comment("Test Comment", "post_id")
        assert str(exc_info.value) == "Not logged in"

def test_post_with_media(strategy):
    """Test post creation with media."""
    with patch.object(strategy, 'is_logged_in', return_value=True), \
         patch.object(strategy, 'post_handler') as mock_handler:
        mock_handler.create_post.return_value = True
        media_files = ["test.jpg"]
        assert strategy.post("Test Content", title="Test Title", media=media_files) is True
        mock_handler.create_post.assert_called_once_with("Test Title", "Test Content", media_files)

class TestRedditStrategy:
    def test_initialization(self, strategy, mock_config, mock_memory_update):
        """Test that strategy initializes with correct components."""
        assert strategy.config == mock_config
        assert strategy.memory_updates == mock_memory_update
        assert hasattr(strategy, 'post_handler')
        assert hasattr(strategy, 'comment_handler')
        assert hasattr(strategy, 'login_handler')
        assert hasattr(strategy, 'media_validator')
        assert hasattr(strategy, 'rate_limiter')

    def test_is_logged_in(self, strategy):
        """Test is_logged_in delegates to login handler."""
        assert strategy.is_logged_in() is True
        strategy.login_handler.is_logged_in.assert_called_once()

    def test_post_success(self, strategy):
        """Test successful post creation."""
        assert strategy.post("Test content") is True
        strategy.post_handler.create_post.assert_called_once_with(
            "Test content", media_paths=None, is_video=False
        )

    def test_post_not_logged_in(self, strategy):
        """Test post attempt when not logged in."""
        strategy.login_handler.is_logged_in.return_value = False
        with pytest.raises(Exception) as exc_info:
            strategy.post("Test content")
        assert str(exc_info.value) == "Not logged in"

    def test_comment_success(self, strategy):
        """Test successful comment creation."""
        assert strategy.comment("Test comment", "post_id") is True
        strategy.comment_handler.create_comment.assert_called_once_with(
            "post_id", "Test comment"
        )

    def test_comment_not_logged_in(self, strategy):
        """Test comment attempt when not logged in."""
        strategy.login_handler.is_logged_in.return_value = False
        with pytest.raises(Exception) as exc_info:
            strategy.comment("Test comment", "post_id")
        assert str(exc_info.value) == "Not logged in" 