import os
import time
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from social.strategies.twitter_strategy import TwitterStrategy
from tests.social.strategies.test_strategy_base import TestStrategyBase

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://twitter.com/home"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "twitter_email": "test@example.com",
        "twitter_password": "test_password"
    }

@pytest.fixture
def mock_memory_update():
    """Create a mock memory update dictionary."""
    return {
        "quest_completions": ["Test Quest"],
        "newly_unlocked_protocols": ["Test Protocol"],
        "feedback_loops_triggered": ["Test Loop"]
    }

@pytest.fixture
def twitter_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a TwitterStrategy instance with mocked dependencies."""
    return TwitterStrategy(mock_driver, mock_config, mock_memory_update)

class TestTwitterStrategy(TestStrategyBase):
    """Twitter strategy test suite."""
    
    @pytest.fixture
    def strategy(self, mock_driver, mock_config):
        return TwitterStrategy(mock_driver, mock_config, {})
    
    def test_initialization(self, strategy):
        """Test Twitter strategy initialization."""
        super().test_init(strategy)
        assert strategy.MAX_POST_LENGTH == 280
        assert strategy.LOGIN_URL == "https://twitter.com/login"
        assert strategy.HOME_URL == "https://twitter.com/home"
        assert strategy.COMPOSE_URL == "https://twitter.com/compose/tweet"
    
    def test_validate_media_video(self, strategy):
        """Test video media validation."""
        with patch.object(strategy.utils, 'validate_media_file', return_value=True):
            assert strategy._validate_media(["test.mp4"], is_video=True) is True
    
    def test_validate_media_multiple_videos(self, strategy):
        """Test multiple video validation."""
        assert strategy._validate_media(["test1.mp4", "test2.mp4"], is_video=True) is False
    
    def test_upload_media_twitter_specific(self, strategy):
        """Test Twitter-specific media upload."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
            assert strategy._upload_media(["test.jpg"]) is True
    
    def test_get_memory_updates(self, strategy):
        """Test memory updates retrieval."""
        updates = strategy.get_memory_updates()
        assert isinstance(updates, dict)
        assert "login_attempts" in updates
        assert "post_attempts" in updates
        assert "media_uploads" in updates
        assert "errors" in updates
        assert "last_action" in updates
        assert "last_error" in updates

def test_initialization(twitter_strategy, mock_driver, mock_config):
    """Test TwitterStrategy initialization."""
    assert twitter_strategy.driver == mock_driver
    assert twitter_strategy.config == mock_config
    assert twitter_strategy.platform == "twitter"
    assert twitter_strategy.utils is not None
    assert twitter_strategy.memory_updates["login_attempts"] == 0
    assert twitter_strategy.memory_updates["post_attempts"] == 0
    assert twitter_strategy.memory_updates["media_uploads"] == 0

def test_is_logged_in_true(twitter_strategy, mock_driver):
    """Test is_logged_in when user is logged in."""
    # Mock element interactions
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # First check
        Mock()  # Timeline found
    ]
    assert twitter_strategy.is_logged_in() is True
    assert twitter_strategy.memory_updates["last_action"] is None

def test_is_logged_in_false(twitter_strategy, mock_driver):
    """Test is_logged_in when user is not logged in."""
    # Mock element interactions
    mock_driver.find_element.side_effect = [
        Mock(),  # Login form found
        NoSuchElementException("Timeline not found")  # Second check
    ]
    assert twitter_strategy.is_logged_in() is False
    assert twitter_strategy.memory_updates["last_action"] is None

def test_is_logged_in_error(twitter_strategy, mock_driver):
    """Test is_logged_in error handling."""
    mock_driver.find_element.side_effect = WebDriverException("Connection error")
    assert twitter_strategy.is_logged_in() is False
    assert twitter_strategy.memory_updates["last_action"]["action"] == "check_login"
    assert twitter_strategy.memory_updates["last_action"]["success"] is False

def test_login_success(twitter_strategy, mock_driver):
    """Test successful login."""
    # Mock element interactions
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Email input
        Mock(),  # Next button
        Mock(),  # Password input
        Mock(),  # Login button
        NoSuchElementException("Login form not found"),  # Final is_logged_in check
        Mock()  # Timeline found
    ]
    
    assert twitter_strategy.login() is True
    assert twitter_strategy.memory_updates["last_action"]["action"] == "login"
    assert twitter_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(twitter_strategy, mock_driver):
    """Test login with missing credentials."""
    twitter_strategy.config = {}
    assert twitter_strategy.login() is False
    assert twitter_strategy.memory_updates["last_action"]["action"] == "login"
    assert twitter_strategy.memory_updates["last_action"]["success"] is False
    assert "Missing credentials" in str(twitter_strategy.memory_updates["last_error"]["error"])

def test_login_failed_attempt(twitter_strategy, mock_driver):
    """Test failed login attempt."""
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # Initial is_logged_in check
        Mock(),  # Email input
        Mock(),  # Next button
        Mock(),  # Password input
        Mock(),  # Login button
        Mock(),  # Login form still present
        NoSuchElementException("Timeline not found")  # Final is_logged_in check
    ]
    
    assert twitter_strategy.login() is False
    assert twitter_strategy.memory_updates["last_action"]["action"] == "login"
    assert twitter_strategy.memory_updates["last_action"]["success"] is False

def test_post_text_success(twitter_strategy, mock_driver):
    """Test successful text post."""
    # Mock element interactions
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Timeline found
        Mock(),  # Post box
        Mock(),  # Post button
        Mock()  # Success indicator
    ]
    
    assert twitter_strategy.post("Test post") is True
    assert twitter_strategy.memory_updates["post_attempts"] == 1
    assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
    assert twitter_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(twitter_strategy, mock_driver):
    """Test successful media post."""
    # Mock element interactions
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Timeline found
        Mock(),  # Post box
        Mock(),  # Media button
        Mock(),  # File input
        Mock(),  # Post button
        Mock()  # Success indicator
    ]
    
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024 * 1024):  # 1MB
        assert twitter_strategy.post("Test post", ["test.jpg"]) is True
        assert twitter_strategy.memory_updates["media_uploads"] == 1
        assert twitter_strategy.memory_updates["post_attempts"] == 1
        assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
        assert twitter_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_validation_failure(twitter_strategy, mock_driver):
    """Test media post with invalid media."""
    with patch("os.path.exists", return_value=False):
        assert twitter_strategy.post("Test post", ["nonexistent.jpg"]) is False
        assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
        assert twitter_strategy.memory_updates["last_action"]["success"] is False
        assert "Invalid media files" in str(twitter_strategy.memory_updates["last_error"]["error"])

def test_post_media_upload_failure(twitter_strategy, mock_driver):
    """Test media post with upload failure."""
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Timeline found
        Mock(),  # Post box
        ElementClickInterceptedException("Upload failed")  # Media button
    ]
    
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024 * 1024):  # 1MB
        assert twitter_strategy.post("Test post", ["test.jpg"]) is False
        assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
        assert twitter_strategy.memory_updates["last_action"]["success"] is False
        assert "Media upload failed" in str(twitter_strategy.memory_updates["last_error"]["error"])

def test_post_timeout(twitter_strategy, mock_driver):
    """Test post with timeout."""
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Timeline found
        TimeoutException("Element not found")  # Post box
    ]
    
    assert twitter_strategy.post("Test post") is False
    assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
    assert twitter_strategy.memory_updates["last_action"]["success"] is False
    assert "Post box not found" in str(twitter_strategy.memory_updates["last_error"]["error"])

def test_post_verification_failure(twitter_strategy, mock_driver):
    """Test post with verification failure."""
    mock_driver.find_element.side_effect = [
        NoSuchElementException("Login form not found"),  # is_logged_in check
        Mock(),  # Timeline found
        Mock(),  # Post box
        Mock(),  # Post button
        TimeoutException("Success indicator not found"),  # Verification
        Mock()  # Still on compose page
    ]
    
    assert twitter_strategy.post("Test post") is False
    assert twitter_strategy.memory_updates["last_action"]["action"] == "post"
    assert twitter_strategy.memory_updates["last_action"]["success"] is False
    assert "Post verification failed" in str(twitter_strategy.memory_updates["last_error"]["error"])

def test_create_post(twitter_strategy):
    """Test post content creation from memory update."""
    content = twitter_strategy.create_post()
    assert "🎯 Quest Complete" in content
    assert "🔓 New Protocols Deployed" in content
    assert "🔄 Feedback Loops Activated" in content
    assert "Test Quest" in content
    assert "Test Protocol" in content
    assert "Test Loop" in content

def test_create_post_no_memory(twitter_strategy):
    """Test post content creation with no memory update."""
    twitter_strategy.memory_update = None
    content = twitter_strategy.create_post()
    assert content == "No memory update available for post creation" 