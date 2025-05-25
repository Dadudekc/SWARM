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

from social.strategies.linkedin_strategy import LinkedInStrategy
from social.utils.social_common import SocialMediaUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://www.linkedin.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "linkedin_email": "test@example.com",
        "linkedin_password": "test_password",
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
def linkedin_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a LinkedInStrategy instance with mocked dependencies."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = LinkedInStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.utils = mock_utils
        return strategy

def test_init(linkedin_strategy, mock_driver, mock_config):
    """Test LinkedInStrategy initialization."""
    assert linkedin_strategy.driver == mock_driver
    assert linkedin_strategy.config == mock_config
    assert linkedin_strategy.platform == "linkedin"
    assert isinstance(linkedin_strategy.memory_updates, dict)
    assert linkedin_strategy.memory_updates["login_attempts"] == 0
    assert linkedin_strategy.memory_updates["post_attempts"] == 0

def test_is_logged_in_true(linkedin_strategy):
    """Test successful login check."""
    linkedin_strategy.utils.wait_for_element.return_value = None
    linkedin_strategy.utils.wait_for_clickable.return_value = Mock()
    
    assert linkedin_strategy.is_logged_in() is True
    linkedin_strategy.utils.wait_for_element.assert_called_once()

def test_is_logged_in_false(linkedin_strategy):
    """Test failed login check."""
    linkedin_strategy.utils.wait_for_element.return_value = Mock()
    
    assert linkedin_strategy.is_logged_in() is False
    linkedin_strategy.utils.wait_for_element.assert_called_once()

def test_login_success(linkedin_strategy):
    """Test successful login."""
    # Mock elements
    email_input = Mock()
    password_input = Mock()
    login_button = Mock()
    
    linkedin_strategy.utils.wait_for_clickable.side_effect = [
        email_input,
        password_input,
        login_button
    ]
    linkedin_strategy.utils.retry_click.return_value = True
    linkedin_strategy.is_logged_in.return_value = True
    
    assert linkedin_strategy.login() is True
    assert linkedin_strategy.memory_updates["login_attempts"] == 1
    assert linkedin_strategy.memory_updates["last_action"]["action"] == "login"
    assert linkedin_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(linkedin_strategy):
    """Test login with missing credentials."""
    linkedin_strategy.config = {}
    
    assert linkedin_strategy.login() is False
    assert "Missing credentials" in str(linkedin_strategy.memory_updates["last_error"]["error"])

def test_login_failure(linkedin_strategy):
    """Test failed login."""
    linkedin_strategy.utils.wait_for_clickable.side_effect = TimeoutException("Element not found")
    
    assert linkedin_strategy.login() is False
    assert linkedin_strategy.memory_updates["last_action"]["success"] is False
    assert "Element not found" in str(linkedin_strategy.memory_updates["last_error"]["error"])

def test_post_text_success(linkedin_strategy):
    """Test successful text post."""
    linkedin_strategy.is_logged_in.return_value = True
    linkedin_strategy.utils.wait_for_clickable.return_value = Mock()
    linkedin_strategy.utils.retry_click.return_value = True
    linkedin_strategy.utils.verify_post_success.return_value = True
    
    content = "Test post content"
    assert linkedin_strategy.post(content) is True
    assert linkedin_strategy.memory_updates["post_attempts"] == 1
    assert linkedin_strategy.memory_updates["last_action"]["action"] == "post"
    assert linkedin_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(linkedin_strategy):
    """Test successful media post."""
    linkedin_strategy.is_logged_in.return_value = True
    linkedin_strategy.utils.wait_for_clickable.return_value = Mock()
    linkedin_strategy.utils.retry_click.return_value = True
    linkedin_strategy.utils.verify_post_success.return_value = True
    linkedin_strategy.utils.validate_linkedin_media.return_value = True
    linkedin_strategy.utils.upload_linkedin_media.return_value = True
    
    content = "Test post with media"
    media_files = ["test_image.jpg"]
    assert linkedin_strategy.post(content, media_files) is True
    assert linkedin_strategy.memory_updates["media_uploads"] == 1

def test_post_not_logged_in(linkedin_strategy):
    """Test post attempt when not logged in."""
    linkedin_strategy.is_logged_in.return_value = False
    linkedin_strategy.login.return_value = False
    
    assert linkedin_strategy.post("Test post") is False
    assert "Not logged in and login failed" in str(linkedin_strategy.memory_updates["last_error"]["error"])

def test_post_media_validation_failure(linkedin_strategy):
    """Test post with invalid media."""
    linkedin_strategy.is_logged_in.return_value = True
    linkedin_strategy.utils.validate_linkedin_media.return_value = False
    
    content = "Test post with invalid media"
    media_files = ["invalid.txt"]
    assert linkedin_strategy.post(content, media_files) is False
    assert "Invalid media files" in str(linkedin_strategy.memory_updates["last_error"]["error"])

def test_create_post(linkedin_strategy, mock_memory_update):
    """Test post content creation from memory update."""
    content = linkedin_strategy.create_post()
    
    assert "Quest Complete!" in content
    assert "New Protocols Deployed:" in content
    assert "Feedback Loops Activated:" in content
    assert "Quest 1" in content
    assert "Protocol 1" in content
    assert "Loop 1" in content

def test_create_post_no_memory(linkedin_strategy):
    """Test post creation with no memory update."""
    linkedin_strategy.memory_update = None
    content = linkedin_strategy.create_post()
    
    assert content == "No memory update available for post creation"

def test_get_memory_updates(linkedin_strategy):
    """Test getting memory updates."""
    memory = linkedin_strategy.get_memory_updates()
    assert isinstance(memory, dict)
    assert "login_attempts" in memory
    assert "post_attempts" in memory
    assert "media_uploads" in memory
    assert "errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory 