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

from social.utils.social_common import SocialMediaUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://test.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "test_key": "test_value"
    }

@pytest.fixture
def social_utils(mock_driver, mock_config):
    """Create a SocialMediaUtils instance with mocked dependencies."""
    return SocialMediaUtils(mock_driver, mock_config, "test_platform")

@patch("os.makedirs")
@patch("os.path.join")
def test_take_screenshot(mock_join, mock_makedirs, social_utils, mock_driver):
    """Test taking a screenshot."""
    mock_join.return_value = "test/path/screenshot.png"
    mock_driver.save_screenshot.return_value = None
    
    filepath = social_utils.take_screenshot("test_context")
    assert "test_platform_test_context_" in filepath
    mock_makedirs.assert_called_once()
    mock_driver.save_screenshot.assert_called_once()

def test_take_screenshot_error(social_utils, mock_driver):
    """Test screenshot error handling."""
    mock_driver.save_screenshot.side_effect = WebDriverException("Screenshot failed")
    assert social_utils.take_screenshot("test_context") is None

def test_retry_click_success(social_utils):
    """Test successful element click."""
    mock_element = Mock()
    assert social_utils.retry_click(mock_element) is True
    mock_element.click.assert_called_once()

def test_retry_click_failure(social_utils):
    """Test failed element click after retries."""
    mock_element = Mock()
    mock_element.click.side_effect = ElementClickInterceptedException("Click failed")
    assert social_utils.retry_click(mock_element) is False
    assert mock_element.click.call_count == 3

def test_validate_media_file_success(social_utils):
    """Test successful media file validation."""
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=1024 * 1024):  # 1MB
        assert social_utils.validate_media_file("test.jpg") is True

def test_validate_media_file_not_found(social_utils):
    """Test media file validation when file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        assert social_utils.validate_media_file("test.jpg") is False

def test_validate_media_file_too_large(social_utils):
    """Test media file validation when file is too large."""
    with patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=21 * 1024 * 1024):  # 21MB
        assert social_utils.validate_media_file("test.jpg") is False

def test_wait_for_element_success(social_utils, mock_driver):
    """Test successful element waiting."""
    mock_element = Mock()
    mock_driver.find_element.return_value = mock_element
    element = social_utils.wait_for_element(By.ID, "test_id")
    assert element == mock_element

def test_wait_for_element_timeout(social_utils, mock_driver):
    """Test element waiting timeout."""
    mock_driver.find_element.side_effect = TimeoutException("Element not found")
    assert social_utils.wait_for_element(By.ID, "test_id") is None

def test_wait_for_clickable_success(social_utils, mock_driver):
    """Test successful clickable element waiting."""
    mock_element = Mock()
    mock_driver.find_element.return_value = mock_element
    element = social_utils.wait_for_clickable(By.ID, "test_id")
    assert element == mock_element

def test_wait_for_clickable_timeout(social_utils, mock_driver):
    """Test clickable element waiting timeout."""
    mock_driver.find_element.side_effect = TimeoutException("Element not found")
    assert social_utils.wait_for_clickable(By.ID, "test_id") is None

def test_format_post_content_no_limit(social_utils):
    """Test post content formatting without length limit."""
    content = "Test content"
    assert social_utils.format_post_content(content) == content

def test_format_post_content_with_limit(social_utils):
    """Test post content formatting with length limit."""
    content = "This is a very long test content that should be truncated"
    formatted = social_utils.format_post_content(content, max_length=20)
    assert len(formatted) == 20
    assert formatted.endswith("...")

def test_create_media_post_content(social_utils):
    """Test media post content creation."""
    with patch("os.path.abspath", return_value="/absolute/path/test.jpg"):
        content = social_utils.create_media_post_content("Test text", ["test.jpg"])
        assert content["text"] == "Test text"
        assert content["media_files"] == ["/absolute/path/test.jpg"]
        assert "timestamp" in content
        assert content["platform"] == "test_platform"

def test_handle_upload_error(social_utils):
    """Test upload error handling."""
    error = WebDriverException("Upload failed")
    assert social_utils.handle_upload_error(error, "test_upload") is False

def test_verify_post_success(social_utils, mock_driver):
    """Test successful post verification."""
    mock_driver.current_url = "https://test.com/post/123"
    assert social_utils.verify_post_success("/post/123") is True

def test_verify_post_failure(social_utils, mock_driver):
    """Test failed post verification."""
    mock_driver.current_url = "https://test.com/other"
    assert social_utils.verify_post_success("/post/123") is False

def test_extract_comment_data_success(social_utils):
    """Test successful comment data extraction."""
    mock_element = Mock()
    mock_element.find_element.side_effect = [
        Mock(text="test_user"),  # author
        Mock(text="Test comment"),  # content
        Mock(text="42")  # score
    ]
    
    data = social_utils.extract_comment_data(mock_element)
    assert data["author"] == "test_user"
    assert data["content"] == "Test comment"
    assert data["score"] == "42"
    assert "timestamp" in data

def test_extract_comment_data_error(social_utils):
    """Test comment data extraction error."""
    mock_element = Mock()
    mock_element.find_element.side_effect = NoSuchElementException("Element not found")
    assert social_utils.extract_comment_data(mock_element) is None 