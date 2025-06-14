# tests/core/social/test_base.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from dreamos.social.strategies.platform_strategy_base import PlatformStrategy, retry_with_recovery

class MockPlatformStrategy(PlatformStrategy):
    """Mock implementation of PlatformStrategy for testing."""
    
    def is_logged_in(self) -> bool:
        return True
        
    def login(self) -> bool:
        return True
        
    def _create_post_impl(self, title: str, content: str, media_files=None) -> bool:
        return True

@pytest.fixture
def mock_driver():
    """Create a mock Selenium WebDriver."""
    driver = Mock(spec=WebDriver)
    driver.find_element = Mock(return_value=Mock(spec=WebElement))
    return driver

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "username": "test_user",
        "password": "test_pass",
        "api_key": "test_key",
        "rate_limits": {
            "posts_per_day": 10,
            "comments_per_day": 50
        }
    }

@pytest.fixture
def platform_strategy(mock_driver, mock_config):
    """Create a PlatformStrategy instance for testing."""
    return MockPlatformStrategy(
        driver=mock_driver,
        config=mock_config,
        memory_update={"stats": {"posts": 0, "comments": 0}},
        agent_id="test_agent"
    )

def test_platform_strategy_initialization(platform_strategy, mock_driver, mock_config):
    """Test proper initialization of PlatformStrategy."""
    assert platform_strategy.driver == mock_driver
    assert platform_strategy.config == mock_config
    assert platform_strategy.agent_id == "test_agent"
    assert platform_strategy.platform == "mockplatform"
    assert isinstance(platform_strategy.memory_updates, dict)
    assert "stats" in platform_strategy.memory_updates

def test_retry_with_recovery_decorator(platform_strategy):
    """Test the retry_with_recovery decorator functionality."""
    
    @retry_with_recovery("test_operation", max_retries=2)
    def failing_operation(self):
        raise Exception("Test error")
    
    # Test that the operation is retried the correct number of times
    with pytest.raises(Exception):
        failing_operation(platform_strategy)
    
    # Verify retry history was updated
    assert len(platform_strategy.memory_updates["retry_history"]) > 0

def test_memory_updates(platform_strategy):
    """Test memory update tracking functionality."""
    # Test updating memory with success
    platform_strategy._update_memory("test_action", True)
    assert platform_strategy.memory_updates["last_action"]["action"] == "test_action"
    assert platform_strategy.memory_updates["last_action"]["success"] is True
    
    # Test updating memory with error
    test_error = Exception("Test error")
    platform_strategy._update_memory("test_action", False, error=test_error)
    assert platform_strategy.memory_updates["last_error"] is not None
    assert "error_type" in platform_strategy.memory_updates["last_error"]

def test_operation_time_tracking(platform_strategy):
    """Test operation time tracking functionality."""
    start_time = datetime.now().timestamp()
    platform_strategy._track_operation_time("test_operation", start_time)
    
    assert "test_operation" in platform_strategy.memory_updates["operation_times"]
    assert len(platform_strategy.memory_updates["operation_times"]["test_operation"]) == 1

def test_media_upload_handling(platform_strategy):
    """Test media upload handling functionality."""
    # Test with valid media paths
    with patch.object(platform_strategy, '_validate_media', return_value=True), \
         patch.object(platform_strategy, '_upload_media', return_value=True):
        result = platform_strategy._handle_media_upload(["test.jpg"])
        assert result is True
        assert platform_strategy.memory_updates["stats"]["media_uploads"] == 1
    
    # Test with invalid media paths
    with patch.object(platform_strategy, '_validate_media', return_value=False):
        result = platform_strategy._handle_media_upload(["invalid.jpg"])
        assert result is False

def test_error_logging(platform_strategy):
    """Test error logging functionality."""
    test_error = Exception("Test error")
    platform_strategy._log_error_with_trace(
        "test_action",
        test_error,
        {"test_context": "value"}
    )
    
    assert platform_strategy.memory_updates["last_error"] is not None
    assert platform_strategy.memory_updates["last_error"]["error_type"] == "Exception"
    assert platform_strategy.memory_updates["last_error"]["action"] == "test_action"

def test_get_memory_updates(platform_strategy):
    """Test getting memory updates."""
    updates = platform_strategy.get_memory_updates()
    assert isinstance(updates, dict)
    assert "stats" in updates
    assert "last_action" in updates
    assert "last_error" in updates
    assert "retry_history" in updates

def test_get_operation_stats(platform_strategy):
    """Test getting operation statistics."""
    # Add some operation times
    platform_strategy._track_operation_time("test_op", datetime.now().timestamp())
    
    stats = platform_strategy.get_operation_stats()
    assert isinstance(stats, dict)
    assert "test_op" in stats
    assert "count" in stats["test_op"]
    assert "avg_time" in stats["test_op"] 