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

from social.strategies.facebook_strategy import FacebookStrategy
from social.utils.social_common import SocialMediaUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://www.facebook.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "facebook_email": "test@example.com",
        "facebook_password": "test_password",
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
def facebook_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a FacebookStrategy instance with mocked dependencies."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = FacebookStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.utils = mock_utils
        return strategy

def test_init(facebook_strategy, mock_driver, mock_config):
    """Test FacebookStrategy initialization."""
    assert facebook_strategy.driver == mock_driver
    assert facebook_strategy.config == mock_config
    assert facebook_strategy.platform == "facebook"
    assert isinstance(facebook_strategy.memory_updates, dict)
    assert facebook_strategy.memory_updates["login_attempts"] == 0
    assert facebook_strategy.memory_updates["post_attempts"] == 0

def test_is_logged_in_true(facebook_strategy):
    """Test successful login check."""
    facebook_strategy.utils.wait_for_element.return_value = None
    facebook_strategy.utils.wait_for_clickable.return_value = Mock()
    
    assert facebook_strategy.is_logged_in() is True
    facebook_strategy.utils.wait_for_element.assert_called_once()

def test_is_logged_in_false(facebook_strategy):
    """Test failed login check."""
    facebook_strategy.utils.wait_for_element.return_value = Mock()
    
    assert facebook_strategy.is_logged_in() is False
    facebook_strategy.utils.wait_for_element.assert_called_once()

def test_login_success(facebook_strategy):
    """Test successful login."""
    # Mock elements
    email_input = Mock()
    password_input = Mock()
    login_button = Mock()
    
    facebook_strategy.utils.wait_for_clickable.side_effect = [
        email_input,
        password_input,
        login_button
    ]
    facebook_strategy.utils.retry_click.return_value = True
    facebook_strategy.is_logged_in.return_value = True
    
    assert facebook_strategy.login() is True
    assert facebook_strategy.memory_updates["login_attempts"] == 1
    assert facebook_strategy.memory_updates["last_action"]["action"] == "login"
    assert facebook_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(facebook_strategy):
    """Test login with missing credentials."""
    facebook_strategy.config = {}
    
    assert facebook_strategy.login() is False
    assert "Missing credentials" in str(facebook_strategy.memory_updates["last_error"]["error"])

def test_login_failure(facebook_strategy):
    """Test failed login."""
    facebook_strategy.utils.wait_for_clickable.side_effect = TimeoutException("Element not found")
    
    assert facebook_strategy.login() is False
    assert facebook_strategy.memory_updates["last_action"]["success"] is False
    assert "Element not found" in str(facebook_strategy.memory_updates["last_error"]["error"])

def test_post_text_success(facebook_strategy):
    """Test successful text post."""
    facebook_strategy.is_logged_in.return_value = True
    facebook_strategy.utils.wait_for_clickable.return_value = Mock()
    facebook_strategy.utils.retry_click.return_value = True
    facebook_strategy.utils.verify_post_success.return_value = True
    
    content = "Test post content"
    assert facebook_strategy.post(content) is True
    assert facebook_strategy.memory_updates["post_attempts"] == 1
    assert facebook_strategy.memory_updates["last_action"]["action"] == "post"
    assert facebook_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(facebook_strategy):
    """Test successful media post."""
    facebook_strategy.is_logged_in.return_value = True
    facebook_strategy.utils.wait_for_clickable.return_value = Mock()
    facebook_strategy.utils.retry_click.return_value = True
    facebook_strategy.utils.verify_post_success.return_value = True
    facebook_strategy.utils.validate_facebook_media.return_value = True
    facebook_strategy.utils.upload_facebook_media.return_value = True
    
    content = "Test post with media"
    media_files = ["test_image.jpg"]
    assert facebook_strategy.post(content, media_files) is True
    assert facebook_strategy.memory_updates["media_uploads"] == 1

def test_post_not_logged_in(facebook_strategy):
    """Test post attempt when not logged in."""
    facebook_strategy.is_logged_in.return_value = False
    facebook_strategy.login.return_value = False
    
    assert facebook_strategy.post("Test post") is False
    assert "Not logged in and login failed" in str(facebook_strategy.memory_updates["last_error"]["error"])

def test_post_media_validation_failure(facebook_strategy):
    """Test post with invalid media."""
    facebook_strategy.is_logged_in.return_value = True
    facebook_strategy.utils.validate_facebook_media.return_value = False
    
    content = "Test post with invalid media"
    media_files = ["invalid.txt"]
    assert facebook_strategy.post(content, media_files) is False
    assert "Invalid media files" in str(facebook_strategy.memory_updates["last_error"]["error"])

def test_create_post(facebook_strategy, mock_memory_update):
    """Test post content creation from memory update."""
    content = facebook_strategy.create_post()
    
    assert "Quest Complete!" in content
    assert "New Protocols Deployed:" in content
    assert "Feedback Loops Activated:" in content
    assert "Quest 1" in content
    assert "Protocol 1" in content
    assert "Loop 1" in content

def test_create_post_no_memory(facebook_strategy):
    """Test post creation with no memory update."""
    facebook_strategy.memory_update = None
    content = facebook_strategy.create_post()
    
    assert content == "No memory update available for post creation"

def test_get_memory_updates(facebook_strategy):
    """Test getting memory updates."""
    memory = facebook_strategy.get_memory_updates()
    assert isinstance(memory, dict)
    assert "login_attempts" in memory
    assert "post_attempts" in memory
    assert "media_uploads" in memory
    assert "errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory 