import os
import time
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

from social.strategies.instagram_strategy import InstagramStrategy
from social.utils.social_common import SocialMediaUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://www.instagram.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "instagram_username": "test_user",
        "instagram_password": "test_password",
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
def instagram_strategy(mock_driver, mock_config, mock_memory_update):
    """Create an InstagramStrategy instance with mocked dependencies."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = InstagramStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.utils = mock_utils
        return strategy

def test_init(instagram_strategy, mock_driver, mock_config):
    """Test InstagramStrategy initialization."""
    assert instagram_strategy.driver == mock_driver
    assert instagram_strategy.config == mock_config
    assert instagram_strategy.platform == "instagram"
    assert isinstance(instagram_strategy.memory_updates, dict)
    assert instagram_strategy.memory_updates["login_attempts"] == 0
    assert instagram_strategy.memory_updates["post_attempts"] == 0

def test_is_logged_in_true(instagram_strategy):
    """Test successful login check."""
    instagram_strategy.utils.wait_for_element.return_value = None
    instagram_strategy.utils.wait_for_clickable.return_value = Mock()
    
    assert instagram_strategy.is_logged_in() is True
    instagram_strategy.utils.wait_for_element.assert_called_once()

def test_is_logged_in_false(instagram_strategy):
    """Test failed login check."""
    instagram_strategy.utils.wait_for_element.return_value = Mock()
    
    assert instagram_strategy.is_logged_in() is False
    instagram_strategy.utils.wait_for_element.assert_called_once()

def test_login_success(instagram_strategy):
    """Test successful login."""
    # Mock elements
    username_input = Mock()
    password_input = Mock()
    login_button = Mock()
    
    instagram_strategy.utils.wait_for_clickable.side_effect = [
        username_input,
        password_input,
        login_button
    ]
    instagram_strategy.utils.retry_click.return_value = True
    instagram_strategy.is_logged_in.return_value = True
    
    assert instagram_strategy.login() is True
    assert instagram_strategy.memory_updates["login_attempts"] == 1
    assert instagram_strategy.memory_updates["last_action"]["action"] == "login"
    assert instagram_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(instagram_strategy):
    """Test login with missing credentials."""
    instagram_strategy.config = {}
    
    assert instagram_strategy.login() is False
    assert "Missing credentials" in str(instagram_strategy.memory_updates["last_error"]["error"])

def test_login_failure(instagram_strategy):
    """Test failed login."""
    instagram_strategy.utils.wait_for_clickable.side_effect = TimeoutException("Element not found")
    
    assert instagram_strategy.login() is False
    assert instagram_strategy.memory_updates["last_action"]["success"] is False
    assert "Element not found" in str(instagram_strategy.memory_updates["last_error"]["error"])

def test_post_text_success(instagram_strategy):
    """Test successful text post."""
    instagram_strategy.is_logged_in.return_value = True
    instagram_strategy.utils.wait_for_clickable.return_value = Mock()
    instagram_strategy.utils.retry_click.return_value = True
    instagram_strategy.utils.verify_post_success.return_value = True
    
    content = "Test post content"
    assert instagram_strategy.post(content) is True
    assert instagram_strategy.memory_updates["post_attempts"] == 1
    assert instagram_strategy.memory_updates["last_action"]["action"] == "post"
    assert instagram_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(instagram_strategy):
    """Test successful media post."""
    instagram_strategy.is_logged_in.return_value = True
    instagram_strategy.utils.wait_for_clickable.return_value = Mock()
    instagram_strategy.utils.retry_click.return_value = True
    instagram_strategy.utils.verify_post_success.return_value = True
    instagram_strategy.utils.validate_instagram_media.return_value = True
    instagram_strategy.utils.upload_instagram_media.return_value = True
    
    content = "Test post with media"
    media_files = ["test_image.jpg"]
    assert instagram_strategy.post(content, media_files) is True
    assert instagram_strategy.memory_updates["media_uploads"] == 1

def test_post_not_logged_in(instagram_strategy):
    """Test post attempt when not logged in."""
    instagram_strategy.is_logged_in.return_value = False
    instagram_strategy.login.return_value = False
    
    assert instagram_strategy.post("Test post") is False
    assert "Not logged in and login failed" in str(instagram_strategy.memory_updates["last_error"]["error"])

def test_post_media_validation_failure(instagram_strategy):
    """Test post with invalid media."""
    instagram_strategy.is_logged_in.return_value = True
    instagram_strategy.utils.validate_instagram_media.return_value = False
    
    content = "Test post with invalid media"
    media_files = ["invalid.txt"]
    assert instagram_strategy.post(content, media_files) is False
    assert "Invalid media files" in str(instagram_strategy.memory_updates["last_error"]["error"])

def test_create_post(instagram_strategy, mock_memory_update):
    """Test post content creation from memory update."""
    content = instagram_strategy.create_post()
    
    assert "Quest Complete!" in content
    assert "New Protocols Deployed:" in content
    assert "Feedback Loops Activated:" in content
    assert "Quest 1" in content
    assert "Protocol 1" in content
    assert "Loop 1" in content

def test_create_post_no_memory(instagram_strategy):
    """Test post creation with no memory update."""
    instagram_strategy.memory_update = None
    content = instagram_strategy.create_post()
    
    assert content == "No memory update available for post creation"

def test_get_memory_updates(instagram_strategy):
    """Test getting memory updates."""
    memory = instagram_strategy.get_memory_updates()
    assert isinstance(memory, dict)
    assert "login_attempts" in memory
    assert "post_attempts" in memory
    assert "media_uploads" in memory
    assert "errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory 