import os
import time
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
import types

from social.strategies.reddit_strategy import RedditStrategy
from social.utils.log_config import LogConfig, LogLevel
from social.constants.platform_constants import (
    REDDIT_MAX_IMAGES,
)

# Remove skip marker to enable tests
# pytestmark = pytest.mark.skip(reason="Strategic bypass - Reddit strategy refactor pending")

@pytest.fixture
def mock_driver():
    driver = Mock()
    driver.current_url = "https://www.reddit.com"
    return driver

@pytest.fixture
def mock_config(tmp_path):
    config = {
        "log_config": LogConfig(
            log_dir=str(tmp_path / "logs"),
            level="INFO",
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ),
        "username": "test_user",
        "password": "test_pass",
        "max_retries": 2,
        "retry_delay": 0,
        "timeout": 1,
        "api_key": "test_api_key",
        "api_secret": "test_api_secret",
        "browser": {
            "headless": False,
            "window_title": "Test Browser",
            "window_coords": {
                "x": 0,
                "y": 0,
                "width": 1024,
                "height": 768
            },
            "cookies_path": str(tmp_path / "cookies")
        }
    }
    # Set additional attributes directly
    config["log_config"].max_size_mb = 10
    config["log_config"].max_age_days = 7
    config["log_config"].batch_size = 100
    config["log_config"].batch_timeout = 60.0
    return config

@pytest.fixture
def mock_memory_update():
    return {
        "last_error": None,
        "stats": {
            "login": 0,
            "post": 0,
            "comment": 0,
            "posts": 0,
            "comments": 0,
            "media_uploads": 0,
            "errors": 0,
            "retries": 0,
            "login_attempts": 0
        },
        "last_action": None,
        "retry_history": [],
        "operation_times": {}
    }

@pytest.fixture
def strategy(mock_driver, mock_config, mock_memory_update):
    strat = RedditStrategy(mock_driver, mock_config, mock_memory_update)
    strat.utils = Mock()  # inject a mocked utils everywhere
    strat.logger = Mock()  # mock the logger
    return strat

@pytest.fixture
def reddit_strategy_fixture(mock_driver, mock_config, mock_memory_update):
    """Fixture for RedditStrategy with real file operations."""
    strat = RedditStrategy(mock_driver, mock_config, mock_memory_update)
    strat.utils = Mock()  # inject a mocked utils everywhere
    strat.logger = Mock()  # mock the logger
    return strat

class TestRedditStrategy:
    def test_initialization(self, strategy, mock_config, mock_memory_update):
        assert strategy.config == mock_config
        assert "last_error" in strategy.memory_updates
        # Check that all required stats keys are present
        for key in mock_memory_update["stats"]:
            assert key in strategy.memory_updates["stats"]
            assert strategy.memory_updates["stats"][key] == mock_memory_update["stats"][key]

    @pytest.mark.parametrize("login_found,menu_found,expected", [
        (False, True, True),
        (True, False, False),
    ])
    def test_is_logged_in(self, strategy, login_found, menu_found, expected, mocker):
        # Mock wait_for_element to simulate login form and user menu presence
        strategy.utils.wait_for_element.side_effect = [
            Mock() if login_found else None,  # login form
            Mock() if menu_found else None    # user menu
        ]
        
        # Mock wait_for_clickable for user menu
        strategy.utils.wait_for_clickable.return_value = Mock()
        
        assert strategy.is_logged_in() is expected
        assert strategy.memory_updates["last_action"] == "is_logged_in"

    @pytest.mark.parametrize("files,is_video,valid", [
        (["a.jpg"], False, True),
        (["a.txt"], False, False),
        (["v.mp4"], True, True),
        (["v.avi"], True, True),
        ([], False, True),
    ])
    def test_validate_media(self, strategy, files, is_video, valid, mocker):
        # Mock file operations
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.getsize", return_value=1024 * 1024)  # 1MB
        
        # Mock splitext to return correct extensions without recursion
        real_splitext = os.path.splitext
        def mock_splitext(path):
            return ("", real_splitext(path)[1])
        mocker.patch("os.path.splitext", side_effect=mock_splitext)
        
        # Set supported formats
        strategy.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        strategy.supported_video_formats = [".mp4", ".mov", ".avi"]
        
        # Set max limits
        strategy.max_images = 20
        strategy.max_videos = 1
        strategy.max_video_size = 100 * 1024 * 1024  # 100MB
        
        assert strategy._validate_media(files, is_video=is_video)[0] == valid

    @pytest.mark.parametrize("test_case", [
        {
            "name": "missing_file",
            "files": ["test.jpg"],
            "exists": False,
            "expected_valid": False,
            "expected_error": "File not found"
        },
        {
            "name": "too_large",
            "files": ["test.jpg"],
            "exists": True,
            "size": 200 * 1024 * 1024,  # 200MB
            "max_size": 100 * 1024 * 1024,  # 100MB
            "expected_valid": False,
            "expected_error": "File too large"
        },
        {
            "name": "too_many_files",
            "files": ["test1.jpg", "test2.jpg"],
            "exists": True,
            "max_files": 1,
            "expected_valid": False,
            "expected_error": "Too many files"
        }
    ])
    def test_validate_media_edge_cases(self, strategy, test_case, mocker):
        # Mock file operations
        mocker.patch("os.path.exists", return_value=test_case.get("exists", True))
        mocker.patch("os.path.getsize", return_value=test_case.get("size", 1024 * 1024))
        
        # Mock splitext to return correct extensions without recursion
        real_splitext = os.path.splitext
        def mock_splitext(path):
            return ("", real_splitext(path)[1])
        mocker.patch("os.path.splitext", side_effect=mock_splitext)
        
        # Set max files if specified
        if "max_files" in test_case:
            strategy.max_images = test_case["max_files"]
            
        # Set max size if specified
        if "max_size" in test_case:
            strategy.max_video_size = test_case["max_size"]
        
        # Run test
        is_valid, error = strategy._validate_media(test_case["files"], is_video=False)
        
        assert is_valid == test_case["expected_valid"]
        assert test_case["expected_error"] in error

    def test_validate_media_real_files(self, strategy, tmp_path):
        """Test media validation with real files."""
        # Create test files
        valid_image = tmp_path / "test.png"
        valid_image.write_text("data")
        
        invalid_format = tmp_path / "test.txt"
        invalid_format.write_text("data")
        
        # Test valid image
        is_valid, error = strategy._validate_media([str(valid_image)], is_video=False)
        assert is_valid is True
        assert error is None
        
        # Test invalid format
        is_valid, error = strategy._validate_media([str(invalid_format)], is_video=False)
        assert is_valid is False
        assert "Unsupported file format" in error

    @pytest.mark.parametrize("method,side_effects,error_context,expected_action,extra_patch", [
        ("login", "Missing credentials", "login", "is_logged_in", None),
        ("post", "Post verification failed", "post", "post", "is_logged_in"),
        ("comment", "Message: Network error\n", "comment", "comment", None),
    ])
    def test_memory_error_tracking(self, strategy, method, side_effects, error_context, expected_action, extra_patch, mocker):
        # For post, mock is_logged_in to True and mock wait_for_element to return a mock for title_input
        if method == "post":
            mocker.patch.object(strategy, "is_logged_in", return_value=True)
            # First call to wait_for_element returns a mock (title_input), then normal
            strategy.utils.wait_for_element.side_effect = [Mock()]
            # retry_click will raise the side_effects exception
            strategy.utils.retry_click.side_effect = ElementClickInterceptedException("Click intercepted")
            result = strategy.post("Test content")
        elif method == "comment":
            # wait_for_element will raise the side_effects exception
            strategy.utils.wait_for_element.side_effect = WebDriverException("Network error")
            result = strategy.comment("http://test.url", "Test comment")
        else:
            # login: mock empty config for missing credentials
            strategy.config = {"reddit": {}}
            result = strategy.login()

        assert result is False
        last = strategy.memory_updates["last_error"]
        assert "error" in last
        assert last["error"] == side_effects
        assert strategy.memory_updates["last_action"] == expected_action

    @pytest.mark.parametrize("first_wait,should_wait_calls", [
        (True, 2),  # When rate limit allows: 1 in post() + 1 in create_post()
        (False, 1),  # When rate limit exceeded: only 1 in post(), never reaches create_post()
    ])
    def test_rate_limiting_flow(self, strategy, first_wait, should_wait_calls, mocker):
        # Mock is_logged_in to return True
        mocker.patch.object(strategy, "is_logged_in", return_value=True)
        
        # Create a mock rate limiter to track calls
        rate_limiter_mock = Mock()
        rate_limiter_mock.check_rate_limit.return_value = first_wait
        
        # Mock the rate limiter at the instance level
        strategy.rate_limiter = rate_limiter_mock
        
        # Mock wait_for_element for post flow
        strategy.utils.wait_for_element.side_effect = [
            Mock(),  # title input
            Mock(),  # content input
            Mock(),  # post button
            Mock(),  # post verification
        ]
        
        # Mock retry_click to succeed
        strategy.utils.retry_click.return_value = True
        
        # Mock _verify_post_success to succeed
        mocker.patch.object(strategy, "_verify_post_success", return_value=True)
        
        # Mock post_handler to be a Mock instance
        strategy.post_handler = Mock()
        strategy.post_handler.create_post.return_value = True
        
        if not first_wait:
            # Should raise rate limit exception
            with pytest.raises(Exception) as exc_info:
                strategy.post("Test post")
            assert "Rate limit exceeded" in str(exc_info.value)
        else:
            # Should succeed
            assert strategy.post("Test post") is True
            
        # Verify rate limiter was called the expected number of times
        assert rate_limiter_mock.check_rate_limit.call_count == should_wait_calls

    def test_post_and_comment_flow(self, strategy, mocker):
        # Mock is_logged_in to return True
        mocker.patch.object(strategy, "is_logged_in", return_value=True)
        
        # Create mock elements for post and comment flow
        title_input = Mock()
        title_input.send_keys = Mock()
        
        content_input = Mock()
        content_input.send_keys = Mock()
        
        post_button = Mock()
        
        comment_box = Mock()
        comment_box.send_keys = Mock()
        
        submit_button = Mock()
        
        # Mock wait_for_element for post and comment flow
        strategy.utils.wait_for_element.side_effect = [
            title_input,  # title input
            content_input,  # content input
            post_button,  # post button
            Mock(),  # post verification
            comment_box,  # comment box
            submit_button,  # comment button
            Mock(),  # comment verification
        ]
        
        # Mock retry_click to succeed
        strategy.utils.retry_click.return_value = True
        
        # Mock _verify_post_success to succeed
        mocker.patch.object(strategy, "_verify_post_success", return_value=True)
        
        # Mock post_handler to be a Mock instance
        strategy.post_handler = Mock()
        strategy.post_handler.create_post.return_value = True
        
        # Mock driver.get to prevent actual navigation
        mocker.patch.object(strategy.driver, "get")
        
        # Test post
        assert strategy.post("Test post") is True
        
        # Test comment
        assert strategy.comment("http://test.url", "Test comment") is True

    def test_validate_media_single_image(self, strategy):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1000):
            is_valid, error = strategy._validate_media(["test.jpg"])
            assert is_valid is True
            assert error is None

    def test_validate_media_empty(self, strategy):
        # Assuming RedditStrategy also considers empty list valid by default from MediaValidator
        is_valid, error = strategy._validate_media([])
        assert is_valid is True 
        assert error is None

    def test_validate_media_unsupported_format(self, strategy):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1000):
            is_valid, error = strategy._validate_media(["test.xyz"])
            assert is_valid is False
            assert "Unsupported file format" in error

    def test_validate_media_too_many_images(self, reddit_strategy_fixture, tmp_path):
        reddit_strategy_fixture.max_images = 1
        images = [tmp_path / "test1.png", tmp_path / "test2.png"]
        for img in images:
            img.write_text("data")
        is_valid, error = reddit_strategy_fixture._validate_media([str(img) for img in images], is_video=False)
        assert is_valid is False
        assert error is not None
        reddit_strategy_fixture.max_images = RedditStrategy.MAX_IMAGES # Reset

    def test_validate_media_invalid_format(self, reddit_strategy_fixture, tmp_path):
        image = tmp_path / "test.txt"
        image.write_text("data")
        is_valid, error = reddit_strategy_fixture._validate_media([str(image)], is_video=False)
        assert is_valid is False
        assert error is not None
