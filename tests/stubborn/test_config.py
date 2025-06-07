import os
import pytest
from pathlib import Path
from dreamos.core.config import ConfigManager

@pytest.fixture
def config():
    return ConfigManager()

def test_config_defaults(config, clean_test_dirs):
    """Test that default config values are set correctly"""
    assert config.log_dir == str(clean_test_dirs / "logs")
    assert os.path.exists(config.log_dir)

def test_config_custom_values(config, clean_test_dirs):
    """Test that custom config values override defaults"""
    custom_log_dir = str(clean_test_dirs / "custom_logs")
    config.log_dir = custom_log_dir
    assert config.log_dir == custom_log_dir
    assert os.path.exists(custom_log_dir)

def test_invalid_log_dir(config):
    """Test that invalid log directory raises ValueError"""
    with pytest.raises(ValueError):
        config.log_dir = "/invalid/path/that/cannot/be/created" 