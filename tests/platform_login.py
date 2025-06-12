"""
Tests for the platform login functionality.
"""

import pytest
from unittest.mock import Mock, patch
from dreamos.social.platform_login import PlatformLoginManager, LoginResult

@pytest.fixture
def login_manager():
    return PlatformLoginManager()

@pytest.fixture
def mock_credentials():
    return {
        "username": "test_user",
        "password": "test_pass",
        "api_key": "test_key"
    }

def test_unsupported_platform(login_manager, mock_credentials):
    """Test login attempt with unsupported platform."""
    result = login_manager.login("unsupported", mock_credentials)
    assert not result.success
    assert result.error == "Unsupported platform"
    assert not result.session_data

@patch("dreamos.social.platform_login.PlatformLoginManager._login_reddit")
def test_reddit_login_success(mock_reddit_login, login_manager, mock_credentials):
    """Test successful Reddit login."""
    mock_reddit_login.return_value = LoginResult(
        success=True,
        session_data={"token": "test_token"}
    )
    
    result = login_manager.login("reddit", mock_credentials)
    assert result.success
    assert result.session_data["token"] == "test_token"
    assert not result.error

@patch("dreamos.social.platform_login.PlatformLoginManager._login_reddit")
def test_reddit_login_failure(mock_reddit_login, login_manager, mock_credentials):
    """Test failed Reddit login."""
    mock_reddit_login.return_value = LoginResult(
        success=False,
        error="Invalid credentials"
    )
    
    result = login_manager.login("reddit", mock_credentials)
    assert not result.success
    assert result.error == "Invalid credentials"
    assert not result.session_data

@patch("dreamos.social.platform_login.PlatformLoginManager._login_twitter")
def test_twitter_login_success(mock_twitter_login, login_manager, mock_credentials):
    """Test successful Twitter login."""
    mock_twitter_login.return_value = LoginResult(
        success=True,
        session_data={"token": "test_token"}
    )
    
    result = login_manager.login("twitter", mock_credentials)
    assert result.success
    assert result.session_data["token"] == "test_token"
    assert not result.error

@patch("dreamos.social.platform_login.PlatformLoginManager._login_twitter")
def test_twitter_login_failure(mock_twitter_login, login_manager, mock_credentials):
    """Test failed Twitter login."""
    mock_twitter_login.return_value = LoginResult(
        success=False,
        error="Rate limit exceeded"
    )
    
    result = login_manager.login("twitter", mock_credentials)
    assert not result.success
    assert result.error == "Rate limit exceeded"
    assert not result.session_data

def test_login_result_creation():
    """Test LoginResult class creation and attributes."""
    # Test with all parameters
    result = LoginResult(
        success=True,
        session_data={"key": "value"},
        error="test error"
    )
    assert result.success
    assert result.session_data == {"key": "value"}
    assert result.error == "test error"
    
    # Test with minimal parameters
    result = LoginResult(success=False)
    assert not result.success
    assert result.session_data == {}
    assert not result.error 