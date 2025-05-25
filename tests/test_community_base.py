import pytest
import json
import os
from pathlib import Path
from social.community.base import CommunityBase

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def base_instance(temp_config_dir, temp_log_dir):
    """Create a CommunityBase instance with temporary directories."""
    return CommunityBase(
        module_name="test_base",
        config_dir=str(temp_config_dir),
        log_dir=str(temp_log_dir)
    )

def test_init(base_instance):
    """Test initialization of CommunityBase."""
    assert base_instance.module_name == "test_base"
    assert isinstance(base_instance.config, dict)
    assert isinstance(base_instance.metrics, dict)

def test_create_default_config(base_instance):
    """Test default configuration creation."""
    config = base_instance._create_default_config()
    assert isinstance(config, dict)
    assert "module_name" in config
    assert "metrics" in config
    assert config["module_name"] == "test_base"

def test_save_config(base_instance, temp_config_dir):
    """Test configuration saving."""
    config = base_instance._create_default_config()
    config_path = temp_config_dir / "test_config.json"
    result = base_instance._save_config(config, str(config_path))
    assert result is True
    assert config_path.exists()

def test_load_config(base_instance, temp_config_dir):
    """Test configuration loading."""
    # First save a config
    config = base_instance._create_default_config()
    config_path = temp_config_dir / "test_config.json"
    base_instance._save_config(config, str(config_path))
    
    # Then load it
    loaded_config = base_instance._load_config(str(config_path))
    assert loaded_config == config

def test_load_nonexistent_config(base_instance):
    """Test loading non-existent configuration."""
    config = base_instance._load_config("nonexistent.json")
    assert config == base_instance._create_default_config()

def test_update_metrics(base_instance):
    """Test metrics updating."""
    metrics = {"test_metric": 1.0}
    base_instance._update_metrics(metrics)
    assert base_instance.metrics["test_metric"] == 1.0 