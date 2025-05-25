import os
import json
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from pathlib import Path

from social.social_config import SocialConfig

@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    with patch('social.utils.log_manager.LogManager') as mock:
        yield mock

@pytest.fixture
def social_config(mock_logger):
    """Create a SocialConfig instance with mocked dependencies."""
    return SocialConfig()

def test_init(social_config):
    """Test SocialConfig initialization."""
    assert isinstance(social_config.config, dict)
    assert social_config.memory_updates["config_loads"] == 0
    assert isinstance(social_config.memory_updates["config_errors"], list)
    assert social_config.memory_updates["last_action"] is None
    assert social_config.memory_updates["last_error"] is None

def test_load_config_success(social_config, mock_logger):
    """Test successful config loading."""
    mock_config = {
        "twitter": {
            "enabled": True,
            "email": "test@example.com",
            "password": "test_password"
        }
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
        with patch('pathlib.Path.exists', return_value=True):
            result = social_config.load_config()
            
            assert result is True
            assert social_config.config == mock_config
            assert social_config.memory_updates["config_loads"] == 1
            assert social_config.memory_updates["last_action"]["action"] == "load_config"
            assert social_config.memory_updates["last_action"]["success"] is True

def test_load_config_file_not_found(social_config, mock_logger):
    """Test config loading when file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = social_config.load_config()
        
        assert result is False
        assert social_config.memory_updates["last_action"]["action"] == "load_config"
        assert social_config.memory_updates["last_action"]["success"] is False
        assert "Config file not found" in str(social_config.memory_updates["last_error"]["error"])

def test_save_config_success(social_config, mock_logger):
    """Test successful config saving."""
    mock_config = {
        "twitter": {
            "enabled": True,
            "email": "test@example.com",
            "password": "test_password"
        }
    }
    social_config.config = mock_config
    
    with patch('builtins.open', mock_open()) as mock_file:
        result = social_config.save_config()
        
        assert result is True
        mock_file.assert_called_once()
        assert social_config.memory_updates["last_action"]["action"] == "save_config"
        assert social_config.memory_updates["last_action"]["success"] is True

def test_save_config_failure(social_config, mock_logger):
    """Test failed config saving."""
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        result = social_config.save_config()
        
        assert result is False
        assert social_config.memory_updates["last_action"]["action"] == "save_config"
        assert social_config.memory_updates["last_action"]["success"] is False
        assert "Permission denied" in str(social_config.memory_updates["last_error"]["error"])

def test_get_config_value(social_config):
    """Test getting config value."""
    social_config.config = {
        "twitter": {
            "enabled": True,
            "email": "test@example.com"
        }
    }
    
    # Test existing value
    assert social_config.get("twitter.enabled") is True
    assert social_config.get("twitter.email") == "test@example.com"
    
    # Test non-existent value with default
    assert social_config.get("twitter.password", "default") == "default"
    assert social_config.get("facebook.enabled", False) is False

def test_set_config_value(social_config):
    """Test setting config value."""
    social_config.set("twitter.enabled", True)
    assert social_config.config["twitter"]["enabled"] is True
    
    social_config.set("twitter.email", "test@example.com")
    assert social_config.config["twitter"]["email"] == "test@example.com"

def test_update_config(social_config):
    """Test updating multiple config values."""
    updates = {
        "twitter": {
            "enabled": True,
            "email": "test@example.com"
        },
        "facebook": {
            "enabled": False
        }
    }
    
    social_config.update(updates)
    assert social_config.config["twitter"]["enabled"] is True
    assert social_config.config["twitter"]["email"] == "test@example.com"
    assert social_config.config["facebook"]["enabled"] is False

def test_get_platform_config(social_config):
    """Test getting platform-specific config."""
    social_config.config = {
        "twitter": {
            "enabled": True,
            "email": "test@example.com"
        },
        "facebook": {
            "enabled": False
        }
    }
    
    twitter_config = social_config.get_platform_config("twitter")
    assert twitter_config["enabled"] is True
    assert twitter_config["email"] == "test@example.com"
    
    facebook_config = social_config.get_platform_config("facebook")
    assert facebook_config["enabled"] is False
    
    # Test non-existent platform
    assert social_config.get_platform_config("instagram") == {}

def test_get_memory_updates(social_config):
    """Test getting memory updates."""
    memory = social_config.get_memory_updates()
    assert isinstance(memory, dict)
    assert "config_loads" in memory
    assert "config_errors" in memory
    assert "last_action" in memory
    assert "last_error" in memory 