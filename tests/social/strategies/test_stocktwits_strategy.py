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

from social.strategies.stocktwits_strategy import StockTwitsStrategy
from social.utils.social_common import SocialMediaUtils

@pytest.fixture
def mock_driver():
    """Create a mock WebDriver instance."""
    driver = Mock()
    driver.current_url = "https://www.stocktwits.com"
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "stocktwits_username": "test_user",
        "stocktwits_password": "test_password",
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
def stocktwits_strategy(mock_driver, mock_config, mock_memory_update):
    """Create a StockTwitsStrategy instance with mocked dependencies."""
    with patch('social.utils.social_common.SocialMediaUtils') as mock_utils:
        strategy = StockTwitsStrategy(mock_driver, mock_config, mock_memory_update)
        strategy.utils = mock_utils
        return strategy

def test_init(stocktwits_strategy, mock_driver, mock_config):
    """Test StockTwitsStrategy initialization."""
    assert stocktwits_strategy.driver == mock_driver
    assert stocktwits_strategy.config == mock_config
    assert stocktwits_strategy.platform == "stocktwits"
    assert isinstance(stocktwits_strategy.memory_updates, dict)
    assert stocktwits_strategy.memory_updates["login_attempts"] == 0
    assert stocktwits_strategy.memory_updates["post_attempts"] == 0

def test_is_logged_in_true(stocktwits_strategy):
    """Test successful login check."""
    stocktwits_strategy.utils.wait_for_element.return_value = None
    stocktwits_strategy.utils.wait_for_clickable.return_value = Mock()
    
    assert stocktwits_strategy.is_logged_in() is True
    stocktwits_strategy.utils.wait_for_element.assert_called_once()

def test_is_logged_in_false(stocktwits_strategy):
    """Test failed login check."""
    stocktwits_strategy.utils.wait_for_element.return_value = Mock()
    
    assert stocktwits_strategy.is_logged_in() is False
    stocktwits_strategy.utils.wait_for_element.assert_called_once()

def test_login_success(stocktwits_strategy):
    """Test successful login."""
    # Mock elements
    username_input = Mock()
    password_input = Mock()
    login_button = Mock()
    
    stocktwits_strategy.utils.wait_for_clickable.side_effect = [
        username_input,
        password_input,
        login_button
    ]
    stocktwits_strategy.utils.retry_click.return_value = True
    stocktwits_strategy.is_logged_in.return_value = True
    
    assert stocktwits_strategy.login() is True
    assert stocktwits_strategy.memory_updates["login_attempts"] == 1
    assert stocktwits_strategy.memory_updates["last_action"]["action"] == "login"
    assert stocktwits_strategy.memory_updates["last_action"]["success"] is True

def test_login_missing_credentials(stocktwits_strategy):
    """Test login with missing credentials."""
    stocktwits_strategy.config = {}
    
    assert stocktwits_strategy.login() is False
    assert "Missing credentials" in str(stocktwits_strategy.memory_updates["last_error"]["error"])

def test_login_failure(stocktwits_strategy):
    """Test failed login."""
    stocktwits_strategy.utils.wait_for_clickable.side_effect = TimeoutException("Element not found")
    
    assert stocktwits_strategy.login() is False
    assert stocktwits_strategy.memory_updates["last_action"]["success"] is False
    assert "Element not found" in str(stocktwits_strategy.memory_updates["last_error"]["error"])

def test_post_text_success(stocktwits_strategy):
    """Test successful text post."""
    stocktwits_strategy.is_logged_in.return_value = True
    stocktwits_strategy.utils.wait_for_clickable.return_value = Mock()
    stocktwits_strategy.utils.retry_click.return_value = True
    stocktwits_strategy.utils.verify_post_success.return_value = True
    
    content = "Test post content"
    assert stocktwits_strategy.post(content) is True
    assert stocktwits_strategy.memory_updates["post_attempts"] == 1
    assert stocktwits_strategy.memory_updates["last_action"]["action"] == "post"
    assert stocktwits_strategy.memory_updates["last_action"]["success"] is True

def test_post_media_success(stocktwits_strategy):
    """Test successful media post."""
    stocktwits_strategy.is_logged_in.return_value = True
    stocktwits_strategy.utils.wait_for_clickable.return_value = Mock()
    stocktwits_strategy.utils.retry_click.return_value = True
    stocktwits_strategy.utils.verify_post_success.return_value = True
    stocktwits_strategy.utils.validate_stocktwits_media.return_value = True
    stocktwits_strategy.utils.upload_stocktwits_media.return_value = True
    
    content = "Test post with media"
    media_files = ["test_image.jpg"]
    assert stocktwits_strategy.post(content, media_files) is True
    assert stocktwits_strategy.memory_updates["media_uploads"] == 1

def test_post_not_logged_in(stocktwits_strategy):
    """Test post attempt when not logged in."""
    stocktwits_strategy.is_logged_in.return_value = False
    stocktwits_strategy.login.return_value = False
    
    assert stocktwits_strategy.post("Test post") is False
    assert "Not logged in and login failed" in str(stocktwits_strategy.memory_updates["last_error"]["error"])

def test_post_media_validation_failure(stocktwits_strategy):
    """Test post with invalid media."""
    stocktwits_strategy.is_logged_in.return_value = True
    stocktwits_strategy.utils.validate_stocktwits_media.return_value = False
    
    content = "Test post with invalid media"
    media_files = ["invalid.txt"]
    assert stocktwits_strategy.post(content, media_files) is False
    assert "Invalid media files" in str(stocktwits_strategy.memory_updates["last_error"]["error"])

def test_create_post(stocktwits_strategy, mock_memory_update):
    """Test post content creation from memory update."""
    content = stocktwits_strategy.create_post()
    
    assert "Quest Complete!" in content
    assert "New Protocols Deployed:" in content
    assert "Feedback Loops Activated:" in content
    assert "Quest 1" in content
    assert "Protocol 1" in content
    assert "Loop 1" in content

def test_create_post_no_memory(stocktwits_strategy):
    """Test post creation with no memory update."""
    stocktwits_strategy.memory_update = None
    content = stocktwits_strategy.create_post()
    
    assert content == "No memory update available for post creation"

def test_get_memory_updates(stocktwits_strategy):
    """Test getting memory updates."""
    memory = stocktwits_strategy.get_memory_updates()
    assert isinstance(memory, dict)
    assert "login_attempts" in memory
    assert "post_attempts" in memory
    assert "media_uploads" in memory
    assert "errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory 