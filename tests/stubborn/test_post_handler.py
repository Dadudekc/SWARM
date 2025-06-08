import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from social.strategies.reddit.handlers.post_handler import PostHandler
from unittest.mock import MagicMock

@pytest.fixture
def mock_driver():
    driver = Mock()
    return driver

@pytest.fixture
def mock_config():
    return {
        "max_retries": 2,
        "retry_delay": 0,
        "timeout": 1
    }

@pytest.fixture
def mock_memory_update():
    return {
        "last_error": None,
        "stats": {"post": 0},
        "last_action": None
    }

@pytest.fixture
def mock_utils():
    """Create a mock SocialMediaUtils instance."""
    utils = Mock()
    utils.wait_for_element = Mock(return_value=Mock())
    utils.wait_for_clickable = Mock(return_value=Mock())
    utils.retry_click = Mock(return_value=True)
    utils.take_screenshot = Mock(return_value="/path/to/screenshot.png")
    return utils

@pytest.fixture
def post_handler(mock_driver, mock_config, mock_memory_update, mock_utils):
    handler = PostHandler(mock_driver, mock_config, mock_memory_update)
    handler.utils = mock_utils
    return handler

class TestPostHandler:
    def test_initialization(self, post_handler, mock_driver, mock_config, mock_memory_update):
        """Test that handler initializes with correct attributes."""
        assert post_handler.driver == mock_driver
        assert post_handler.config == mock_config
        assert post_handler.memory_update == mock_memory_update
        assert isinstance(post_handler.selectors, dict)
        assert "post_button" in post_handler.selectors
        assert "title_input" in post_handler.selectors
        assert "content_input" in post_handler.selectors
        assert "submit_button" in post_handler.selectors
        assert "post_verification" in post_handler.selectors

    def test_create_post_success(self, post_handler):
        """Test successful post creation."""
        # Mock driver elements
        post_button = MagicMock()
        text_area = MagicMock()
        submit_button = MagicMock()
        
        # Set up mock chain
        post_handler.driver.find_element.side_effect = [
            post_button,  # Post button
            text_area,    # Text area
            submit_button # Submit button
        ]
        
        # Create post
        result = post_handler.create_post("Test content")
        
        # Verify result
        assert result is True
        assert post_handler.driver.find_element.call_count == 3
        
        # Verify interactions
        post_button.click.assert_called_once()
        text_area.send_keys.assert_called_once_with("Test content")
        submit_button.click.assert_called_once()

    def test_create_post_timeout(self, post_handler):
        """Test post creation fails on timeout."""
        post_handler.utils.wait_for_element.side_effect = TimeoutException("Element not found")
        
        assert post_handler.create_post("Test content") is False
        assert "Element not found" in post_handler.memory_update["last_error"]["error"]

    def test_create_post_click_intercepted(self, post_handler):
        """Test post creation when click is intercepted."""
        # Mock driver to simulate click interception
        post_handler.driver.find_element.side_effect = [
            MagicMock(),  # Post button
            MagicMock(),  # Text area
            MagicMock(),  # Submit button
            Exception("Click intercepted")  # Simulate click interception
        ]
        
        # Attempt to create post
        result = post_handler.create_post("Test content")
        
        # Verify result
        assert result is False
        assert post_handler.driver.find_element.call_count == 4

    def test_create_post_with_media(self, post_handler):
        """Test post creation with media."""
        # Mock driver elements
        post_button = MagicMock()
        text_area = MagicMock()
        media_button = MagicMock()
        file_input = MagicMock()
        submit_button = MagicMock()
        
        # Set up mock chain
        post_handler.driver.find_element.side_effect = [
            post_button,   # Post button
            text_area,     # Text area
            media_button,  # Media button
            file_input,    # File input
            submit_button  # Submit button
        ]
        
        # Create post with media
        result = post_handler.create_post("Test content", media_paths=["test.jpg"])
        
        # Verify result
        assert result is True
        assert post_handler.driver.find_element.call_count == 5
        
        # Verify interactions
        post_button.click.assert_called_once()
        text_area.send_keys.assert_called_once_with("Test content")
        media_button.click.assert_called_once()
        file_input.send_keys.assert_called_once_with("test.jpg")
        submit_button.click.assert_called_once() 
