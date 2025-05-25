import os
import json
import pickle
import pytest
from unittest.mock import patch, mock_open
from social.driver.session_state import SessionState

@pytest.fixture
def session_state():
    """Create a SessionState instance for testing."""
    return SessionState("test_session")

@pytest.fixture
def mock_session_data():
    """Sample session data for testing."""
    return {
        "platforms": {
            "facebook": {
                "status": "logged_in",
                "last_updated": 1234567890,
                "details": {"user_id": "123"}
            }
        },
        "last_successful_login": 1234567890,
        "failed_attempts": {},
        "proxy_history": [],
        "performance_metrics": {
            "avg_load_time": 1.5,
            "success_rate": 0.95,
            "total_requests": 100
        }
    }

def test_init_creates_default_state(session_state):
    """Test that initialization creates default state structure."""
    assert "platforms" in session_state.session_data
    assert "last_successful_login" in session_state.session_data
    assert "failed_attempts" in session_state.session_data
    assert "proxy_history" in session_state.session_data
    assert "performance_metrics" in session_state.session_data

@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open, read_data="{}")
def test_load_state_file_exists(mock_file, mock_exists, session_state):
    """Test loading state from existing file."""
    mock_exists.return_value = True
    session_state._load_state()
    mock_file.assert_called_once()

@patch("os.path.exists")
def test_load_state_file_not_exists(mock_exists, session_state):
    """Test handling when state file doesn't exist."""
    mock_exists.return_value = False
    session_state._load_state()
    assert session_state.session_data["platforms"] == {}

@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_save_state(mock_file, mock_makedirs, session_state):
    """Test saving state to file."""
    session_state.save_state()
    mock_makedirs.assert_called_once()
    mock_file.assert_called_once()

def test_update_platform_state(session_state):
    """Test updating platform state."""
    platform = "facebook"
    status = "logged_in"
    details = {"user_id": "123"}
    
    session_state.update_platform_state(platform, status, details)
    
    platform_state = session_state.get_platform_state(platform)
    assert platform_state["status"] == status
    assert platform_state["details"] == details

def test_get_platform_state_nonexistent(session_state):
    """Test getting state for non-existent platform."""
    assert session_state.get_platform_state("nonexistent") is None

@patch("os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_save_cookies(mock_file, mock_makedirs, session_state):
    """Test saving cookies."""
    cookies = [{"name": "test", "value": "cookie"}]
    session_state.save_cookies(cookies)
    mock_makedirs.assert_called_once()
    mock_file.assert_called_once()

@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open, read_data=pickle.dumps([{"name": "test", "value": "cookie"}]))
def test_load_cookies(mock_file, mock_exists, session_state):
    """Test loading cookies."""
    mock_exists.return_value = True
    cookies = session_state.load_cookies()
    assert cookies == [{"name": "test", "value": "cookie"}]

@patch("os.path.exists")
def test_load_cookies_file_not_exists(mock_exists, session_state):
    """Test handling when cookies file doesn't exist."""
    mock_exists.return_value = False
    assert session_state.load_cookies() is None 