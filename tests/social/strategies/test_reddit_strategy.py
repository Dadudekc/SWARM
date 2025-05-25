import os
import time
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from social.strategies.reddit_strategy import RedditStrategy
from social.utils.social_common import SocialMediaUtils
from social.constants.platform_constants import (
    REDDIT_MAX_IMAGES,
    REDDIT_SUPPORTED_IMAGE_FORMATS,
    REDDIT_SUPPORTED_VIDEO_FORMATS
)
from tests.social.strategies.test_strategy_base import TestStrategyBase

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://www.reddit.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "reddit_username": "test_user",
        "reddit_password": "test_password",
        "headless": False,
        "timeout": 30
    }

@pytest.fixture
def mock_memory_update():
    """Create a mock memory update."""
    return {
        "quest_completions": ["Quest 1", "Quest 2"],
        "newly_unlocked_protocols": ["Protocol 1", "Protocol 2"],
        "feedback_loops_triggered": ["Loop 1", "Loop 2"]
    }

@pytest.fixture
def reddit_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a RedditStrategy instance with mocked dependencies."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = RedditStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.utils = mock_utils
        return strategy

class TestRedditStrategy(TestStrategyBase):
    """Reddit strategy test suite."""
    
    @pytest.fixture
    def strategy(self, mock_driver, mock_config):
        return RedditStrategy(mock_driver, mock_config, {})
    
    def test_initialization(self, strategy):
        """Test Reddit strategy initialization."""
        super().test_init(strategy)
        assert strategy.LOGIN_URL == "https://www.reddit.com/login"
        assert strategy.HOME_URL == "https://www.reddit.com"
        assert strategy.subreddit == "test_subreddit"
    
    def test_validate_media_video(self, strategy):
        """Test video media validation."""
        with patch.object(strategy.utils, 'validate_media_file', return_value=True):
            assert strategy._validate_media(["test.mp4"], is_video=True) is True
    
    def test_validate_media_multiple_videos(self, strategy):
        """Test multiple video validation."""
        assert strategy._validate_media(["test1.mp4", "test2.mp4"], is_video=True) is False
    
    def test_upload_media_reddit_specific(self, strategy):
        """Test Reddit-specific media upload."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
            with patch.object(strategy.utils, 'retry_click', return_value=True):
                with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                    assert strategy._upload_media(["test.jpg"]) is True
    
    def test_comment_success(self, strategy):
        """Test successful comment."""
        with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
            with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                with patch.object(strategy.utils, 'retry_click', return_value=True):
                    assert strategy.comment("https://reddit.com/test", "Test comment") is True
    
    def test_comment_verification_failed(self, strategy):
        """Test comment with failed verification."""
        with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
            with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                with patch.object(strategy.utils, 'retry_click', return_value=True):
                    with patch.object(strategy.driver, 'find_element', side_effect=NoSuchElementException()):
                        assert strategy.comment("https://reddit.com/test", "Test comment") is False
    
    def test_get_post_comments_success(self, strategy):
        """Test successful comment retrieval."""
        mock_comment = Mock()
        mock_comment.text = "Test comment"
        mock_comment.get_attribute.return_value = "test_user"
        
        with patch.object(strategy.utils, 'wait_for_elements', return_value=[mock_comment]):
            with patch.object(strategy.utils, 'extract_comment_data', return_value={"text": "Test comment", "author": "test_user"}):
                comments = strategy.get_post_comments("https://reddit.com/test")
                assert len(comments) == 1
                assert comments[0]["text"] == "Test comment"
                assert comments[0]["author"] == "test_user"
    
    def test_get_post_comments_error(self, strategy):
        """Test comment retrieval with error."""
        with patch.object(strategy.utils, 'wait_for_elements', side_effect=Exception("Test error")):
            comments = strategy.get_post_comments("https://reddit.com/test")
            assert len(comments) == 0

def test_init(reddit_strategy, mock_driver, mock_config):
    """Test RedditStrategy initialization."""
    assert reddit_strategy.driver == mock_driver
    assert reddit_strategy.config == mock_config
    assert reddit_strategy.platform == "reddit"
    assert isinstance(reddit_strategy.memory_updates, dict)
    assert reddit_strategy.memory_updates["login_attempts"] == 0
    assert reddit_strategy.memory_updates["post_attempts"] == 0

def test_is_logged_in_true(reddit_strategy):
    """Test successful login check."""
    reddit_strategy.utils.wait_for_element.return_value = None
    reddit_strategy.utils.wait_for_clickable.return_value = Mock()
    
    assert reddit_strategy.is_logged_in() is True
    reddit_strategy.utils.wait_for_element.assert_called_once()

def test_is_logged_in_false(reddit_strategy):
    """Test failed login check."""
    reddit_strategy.utils.wait_for_element.return_value = Mock()
    
    assert reddit_strategy.is_logged_in() is False
    reddit_strategy.utils.wait_for_element.assert_called_once()

def test_login_success(reddit_strategy):
    """Test successful login."""
    # Mock elements
    username_input = Mock()
    password_input = Mock()
    login_button = Mock()
    
    reddit_strategy.utils.wait_for_clickable.side_effect = [
        username_input,
        password_input,
        login_button
    ]
    reddit_strategy.utils.retry_click.return_value = True
    reddit_strategy.is_logged_in.return_value = True
    
    assert reddit_strategy.login() is True
    assert reddit_strategy.memory_updates["login_attempts"] == 1
    assert reddit_strategy.memory_updates["last_action"]["action"] == "login"
    assert reddit_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(reddit_strategy):
    """Test login with missing credentials."""
    reddit_strategy.config = {}
    
    assert reddit_strategy.login() is False
    assert "Missing credentials" in str(reddit_strategy.memory_updates["last_error"]["error"])

def test_login_failure(reddit_strategy):
    """Test failed login."""
    reddit_strategy.utils.wait_for_clickable.side_effect = TimeoutException("Element not found")
    
    assert reddit_strategy.login() is False
    assert reddit_strategy.memory_updates["last_action"]["success"] is False
    assert "Element not found" in str(reddit_strategy.memory_updates["last_error"]["error"])

def test_post_text_success(reddit_strategy):
    """Test successful text post."""
    reddit_strategy.is_logged_in.return_value = True
    reddit_strategy.utils.wait_for_clickable.return_value = Mock()
    reddit_strategy.utils.retry_click.return_value = True
    reddit_strategy.utils.verify_post_success.return_value = True
    
    content = "Test post content"
    assert reddit_strategy.post(content) is True
    assert reddit_strategy.memory_updates["post_attempts"] == 1
    assert reddit_strategy.memory_updates["last_action"]["action"] == "post"
    assert reddit_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(reddit_strategy):
    """Test successful media post."""
    reddit_strategy.is_logged_in.return_value = True
    reddit_strategy.utils.wait_for_clickable.return_value = Mock()
    reddit_strategy.utils.retry_click.return_value = True
    reddit_strategy.utils.verify_post_success.return_value = True
    reddit_strategy.utils.validate_reddit_media.return_value = True
    reddit_strategy.utils.upload_reddit_media.return_value = True
    
    content = "Test post with media"
    media_files = ["test_image.jpg"]
    assert reddit_strategy.post(content, media_files) is True
    assert reddit_strategy.memory_updates["media_uploads"] == 1

def test_post_not_logged_in(reddit_strategy):
    """Test post attempt when not logged in."""
    reddit_strategy.is_logged_in.return_value = False
    reddit_strategy.login.return_value = False
    
    assert reddit_strategy.post("Test post") is False
    assert "Not logged in and login failed" in str(reddit_strategy.memory_updates["last_error"]["error"])

def test_post_media_validation_failure(reddit_strategy):
    """Test post with invalid media."""
    reddit_strategy.is_logged_in.return_value = True
    reddit_strategy.utils.validate_reddit_media.return_value = False
    
    content = "Test post with invalid media"
    media_files = ["invalid.txt"]
    assert reddit_strategy.post(content, media_files) is False
    assert "Invalid media files" in str(reddit_strategy.memory_updates["last_error"]["error"])

def test_create_post(reddit_strategy, mock_memory_update):
    """Test post content creation from memory update."""
    content = reddit_strategy.create_post()
    
    assert "Quest Complete!" in content
    assert "New Protocols Deployed:" in content
    assert "Feedback Loops Activated:" in content
    assert "Quest 1" in content
    assert "Protocol 1" in content
    assert "Loop 1" in content

def test_create_post_no_memory(reddit_strategy):
    """Test post creation with no memory update."""
    reddit_strategy.memory_update = None
    content = reddit_strategy.create_post()
    
    assert content == "No memory update available for post creation"

def test_get_memory_updates(reddit_strategy):
    """Test getting memory updates."""
    memory = reddit_strategy.get_memory_updates()
    assert isinstance(memory, dict)
    assert "login_attempts" in memory
    assert "post_attempts" in memory
    assert "media_uploads" in memory
    assert "errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory

@patch("os.makedirs")
@patch("os.path.join")
def test_take_screenshot(mock_join, mock_makedirs, reddit_strategy, mock_driver):
    """Test taking a screenshot."""
    mock_join.return_value = "test/path/screenshot.png"
    mock_driver.save_screenshot.return_value = None
    
    filepath = reddit_strategy._take_screenshot("test_context")
    assert "reddit_test_context_" in filepath
    mock_makedirs.assert_called_once()
    mock_driver.save_screenshot.assert_called_once()

def test_take_screenshot_error(reddit_strategy, mock_driver):
    """Test screenshot error handling."""
    mock_driver.save_screenshot.side_effect = WebDriverException("Screenshot failed")
    assert reddit_strategy._take_screenshot("test_context") is None

def test_retry_click_success(reddit_strategy):
    """Test successful element click."""
    mock_element = Mock()
    assert reddit_strategy._retry_click(mock_element) is True
    mock_element.click.assert_called_once()

def test_retry_click_failure(reddit_strategy):
    """Test failed element click after retries."""
    mock_element = Mock()
    mock_element.click.side_effect = ElementClickInterceptedException("Click failed")
    assert reddit_strategy._retry_click(mock_element) is False
    assert mock_element.click.call_count == 3

def test_validate_media_empty(reddit_strategy):
    assert reddit_strategy._validate_media([]) is True

def test_validate_media_single_image(reddit_strategy):
    with patch.object(reddit_strategy.utils, 'validate_media_file', return_value=True):
        assert reddit_strategy._validate_media(["test.jpg"]) is True

def test_validate_media_too_many_images(reddit_strategy):
    images = ["test.jpg"] * (REDDIT_MAX_IMAGES + 1)
    assert reddit_strategy._validate_media(images) is False

def test_validate_media_unsupported_format(reddit_strategy):
    assert reddit_strategy._validate_media(["test.xyz"]) is False

def test_post_text_success(reddit_strategy, mock_driver):
    """Test successful text post creation."""
    # Mock the post form elements
    mock_driver.find_element.side_effect = [
        Mock(),  # text post button
        Mock(),  # title input
        Mock(),  # content input
        Mock()   # post button
    ]
    
    # Mock successful post URL
    mock_driver.current_url = "https://www.reddit.com/r/test_subreddit/comments/123"
    
    assert reddit_strategy.post("Test content") is True

def test_post_media_success(reddit_strategy, mock_driver):
    """Test successful media post creation."""
    # Mock the post form elements
    mock_driver.find_element.side_effect = [
        Mock(),  # media post button
        Mock(),  # file input
        Mock(),  # title input
        Mock(),  # content input
        Mock()   # post button
    ]
    
    # Mock successful post URL
    mock_driver.current_url = "https://www.reddit.com/r/test_subreddit/comments/123"
    
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024 * 1024), \
         patch("os.path.abspath", return_value="/absolute/path/test.jpg"):
        assert reddit_strategy.post("Test content", ["test.jpg"]) is True

def test_post_media_validation_failed(reddit_strategy, mock_driver):
    """Test media post with failed validation."""
    with patch("os.path.exists", return_value=False):
        assert reddit_strategy.post("Test content", ["test.jpg"]) is False

def test_post_failed_verification(reddit_strategy, mock_driver):
    """Test post with failed URL verification."""
    # Mock the post form elements
    mock_driver.find_element.side_effect = [
        Mock(),  # text post button
        Mock(),  # title input
        Mock(),  # content input
        Mock()   # post button
    ]
    
    # Mock incorrect post URL
    mock_driver.current_url = "https://www.reddit.com/r/test_subreddit"
    
    assert reddit_strategy.post("Test content") is False

def test_post_timeout(reddit_strategy, mock_driver):
    """Test post with timeout error."""
    mock_driver.find_element.side_effect = TimeoutException("Element not found")
    assert reddit_strategy.post("Test content") is False

def test_comment_timeout(reddit_strategy, mock_driver):
    """Test comment with timeout error."""
    mock_driver.find_element.side_effect = TimeoutException("Element not found")
    assert reddit_strategy.comment("https://reddit.com/post/123", "Test comment") is False

def test_create_post(reddit_strategy):
    """Test post content creation from memory update."""
    content = reddit_strategy.create_post()
    assert "Test Quest" in content
    assert "Test Protocol" in content
    assert "Test Loop" in content 