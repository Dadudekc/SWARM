import pytest
from unittest.mock import Mock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from social.utils.social_common import SocialMediaUtils
from social.constants.platform_constants import (
    MAX_RETRIES,
    RETRY_DELAY
)

class TestStrategyBase:
    """Base test class for platform strategies."""
    
    @pytest.fixture
    def mock_driver(self):
        driver = Mock()
        driver.find_element.return_value = Mock()
        return driver
    
    @pytest.fixture
    def mock_config(self):
        return {
            "username": "test_user",
            "password": "test_pass"
        }
    
    def test_init(self, strategy):
        """Test strategy initialization."""
        assert strategy.platform is not None
        assert isinstance(strategy.utils, SocialMediaUtils)
    
    def test_validate_media_empty(self, strategy):
        """Test media validation with empty list."""
        assert strategy._validate_media([]) is True
    
    def test_validate_media_single_image(self, strategy):
        """Test media validation with single image."""
        with patch.object(strategy.utils, 'validate_media_file', return_value=True):
            assert strategy._validate_media(["test.jpg"]) is True
    
    def test_validate_media_unsupported_format(self, strategy):
        """Test media validation with unsupported format."""
        assert strategy._validate_media(["test.xyz"]) is False
    
    def test_upload_media_success(self, strategy):
        """Test successful media upload."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
            with patch.object(strategy.utils, 'retry_click', return_value=True):
                with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                    assert strategy._upload_media(["test.jpg"]) is True
    
    def test_upload_media_button_not_found(self, strategy):
        """Test media upload with missing button."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=None):
            assert strategy._upload_media(["test.jpg"]) is False
    
    def test_upload_media_click_failed(self, strategy):
        """Test media upload with failed click."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
            with patch.object(strategy.utils, 'retry_click', return_value=False):
                assert strategy._upload_media(["test.jpg"]) is False
    
    def test_upload_media_file_input_not_found(self, strategy):
        """Test media upload with missing file input."""
        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
            with patch.object(strategy.utils, 'retry_click', return_value=True):
                with patch.object(strategy.utils, 'wait_for_element', return_value=None):
                    assert strategy._upload_media(["test.jpg"]) is False
    
    def test_is_logged_in_true(self, strategy):
        """Test successful login check."""
        strategy.driver.find_element.side_effect = NoSuchElementException()
        assert strategy.is_logged_in() is True
    
    def test_is_logged_in_false(self, strategy):
        """Test failed login check."""
        strategy.driver.find_element.return_value = Mock()
        assert strategy.is_logged_in() is False
    
    def test_login_success(self, strategy):
        """Test successful login."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                    with patch.object(strategy.utils, 'retry_click', return_value=True):
                        assert strategy.login() is True
    
    def test_login_missing_credentials(self, strategy):
        """Test login with missing credentials."""
        strategy.config = {}
        assert strategy.login() is False
    
    def test_login_input_not_found(self, strategy):
        """Test login with missing input field."""
        with patch.object(strategy.utils, 'wait_for_element', return_value=None):
            assert strategy.login() is False
    
    def test_login_button_click_failed(self, strategy):
        """Test login with failed button click."""
        with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
            with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                with patch.object(strategy.utils, 'retry_click', return_value=False):
                    assert strategy.login() is False
    
    def test_login_verification_failed(self, strategy):
        """Test login with failed verification."""
        with patch.object(strategy, 'is_logged_in', return_value=False):
            with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                    with patch.object(strategy.utils, 'retry_click', return_value=True):
                        assert strategy.login() is False
    
    def test_post_success(self, strategy):
        """Test successful post."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy, '_validate_media', return_value=True):
                with patch.object(strategy, '_upload_media', return_value=True):
                    with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                            with patch.object(strategy.utils, 'retry_click', return_value=True):
                                with patch.object(strategy.utils, 'verify_post_success', return_value=True):
                                    assert strategy.post("Test content", ["test.jpg"]) is True
    
    def test_post_not_logged_in(self, strategy):
        """Test post without login."""
        with patch.object(strategy, 'is_logged_in', return_value=False):
            with patch.object(strategy, 'login', return_value=False):
                assert strategy.post("Test content") is False
    
    def test_post_media_validation_failed(self, strategy):
        """Test post with failed media validation."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy, '_validate_media', return_value=False):
                assert strategy.post("Test content", ["test.jpg"]) is False
    
    def test_post_media_upload_failed(self, strategy):
        """Test post with failed media upload."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy, '_validate_media', return_value=True):
                with patch.object(strategy, '_upload_media', return_value=False):
                    assert strategy.post("Test content", ["test.jpg"]) is False
    
    def test_post_button_not_found(self, strategy):
        """Test post with missing button."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy, '_validate_media', return_value=True):
                with patch.object(strategy, '_upload_media', return_value=True):
                    with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                        with patch.object(strategy.utils, 'wait_for_clickable', return_value=None):
                            assert strategy.post("Test content") is False
    
    def test_post_verification_failed(self, strategy):
        """Test post with failed verification."""
        with patch.object(strategy, 'is_logged_in', return_value=True):
            with patch.object(strategy, '_validate_media', return_value=True):
                with patch.object(strategy, '_upload_media', return_value=True):
                    with patch.object(strategy.utils, 'wait_for_element', return_value=Mock()):
                        with patch.object(strategy.utils, 'wait_for_clickable', return_value=Mock()):
                            with patch.object(strategy.utils, 'retry_click', return_value=True):
                                with patch.object(strategy.utils, 'verify_post_success', return_value=False):
                                    assert strategy.post("Test content") is False 