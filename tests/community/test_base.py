import pytest
import json
import os
from pathlib import Path
from social.community.base import CommunityBase
import win32security
import win32file
import win32con
import win32api

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

def test_save_config_permission_error(tmp_path):
    """Test handling of permission errors when saving config."""
    # Create config directory and base instance first
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    base_instance = CommunityBase(
        module_name="test_base",
        config_dir=str(config_dir),
        log_dir=str(tmp_path)
    )
    
    config_path = config_dir / "test_config.json"
    config = {"test": "config"}
    
    # Get current security info
    security_info = win32security.GetFileSecurity(
        str(config_dir),
        win32security.DACL_SECURITY_INFORMATION
    )
    dacl = security_info.GetSecurityDescriptorDacl()
    
    # Create a new DACL that denies write access
    everyone_sid = win32security.ConvertStringSidToSid("S-1-1-0")
    dacl.AddAccessDeniedAce(
        win32security.ACL_REVISION,
        win32con.GENERIC_WRITE,
        everyone_sid
    )
    
    # Apply the new DACL
    security_info.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        str(config_dir),
        win32security.DACL_SECURITY_INFORMATION,
        security_info
    )
    
    try:
        with pytest.raises(PermissionError):
            base_instance._save_config(config, str(config_path))
    finally:
        # Restore permissions by removing the deny ACE
        security_info = win32security.GetFileSecurity(
            str(config_dir),
            win32security.DACL_SECURITY_INFORMATION
        )
        dacl = security_info.GetSecurityDescriptorDacl()
        dacl.DeleteAce(0)  # Remove the deny ACE we added
        security_info.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(
            str(config_dir),
            win32security.DACL_SECURITY_INFORMATION,
            security_info
        )

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

def test_load_invalid_config(base_instance, temp_config_dir):
    """Test loading invalid configuration."""
    config_path = temp_config_dir / "invalid_config.json"
    with open(config_path, 'w') as f:
        f.write("invalid json content")
    
    config = base_instance._load_config(str(config_path))
    assert config == base_instance._create_default_config()

def test_update_metrics(base_instance):
    """Test metrics updating."""
    metrics = {"test_metric": 1.0}
    base_instance._update_metrics(metrics)
    assert base_instance.metrics["test_metric"] == 1.0

def test_update_metrics_invalid_type(base_instance):
    """Test metrics updating with invalid type."""
    metrics = ["invalid_metrics"]
    with pytest.raises(ValueError):
        base_instance._update_metrics(metrics)

def test_update_metrics_nested(base_instance):
    """Test updating nested metrics."""
    metrics = {
        "nested": {
            "metric1": 1.0,
            "metric2": 2.0
        }
    }
    base_instance._update_metrics(metrics)
    assert base_instance.metrics["nested"]["metric1"] == 1.0
    assert base_instance.metrics["nested"]["metric2"] == 2.0 