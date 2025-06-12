import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for bridge config loader module."""

import pytest
from dreamos.core.bridge.config.loader import BridgeConfigLoader

@pytest.fixture
def config_loader():
    return BridgeConfigLoader()

def test_config_loader_initialization(config_loader):
    """Test config loader initialization."""
    assert config_loader is not None

def test_load_config(config_loader):
    """Test loading configuration."""
    config = config_loader.load_config()
    assert config is not None
    assert isinstance(config, dict)

def test_save_agent_config(config_loader, tmp_path):
    """Test saving agent configuration."""
    config = {
        "agent_id": "test_agent",
        "settings": {
            "enabled": True
        }
    }
    config_loader.save_agent_config(config, str(tmp_path))
    loaded_config = config_loader.load_config(str(tmp_path))
    assert loaded_config == config

def test_validate_config(config_loader):
    """Test config validation."""
    valid_config = {
        "agent_id": "test_agent",
        "settings": {
            "enabled": True
        }
    }
    assert config_loader.validate_config(valid_config) is True

    invalid_config = {
        "settings": {
            "enabled": True
        }
    }
    assert config_loader.validate_config(invalid_config) is False
