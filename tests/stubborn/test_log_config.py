"""Tests for unified logging configuration."""

import pytest
from datetime import datetime, timedelta
import os
import json
from dreamos.core.logging.log_config import (
    LogLevel,
    LogConfig,
    DEFAULT_CONFIG,
    get_log_path,
    get_metrics_path,
    get_retention_date
)

def test_log_level_ordering():
    """Test log level ordering and threshold checks."""
    assert LogLevel.DEBUG.should_log(LogLevel.DEBUG) is True
    assert LogLevel.INFO.should_log(LogLevel.DEBUG) is True
    assert LogLevel.DEBUG.should_log(LogLevel.INFO) is False
    assert LogLevel.ERROR.should_log(LogLevel.WARNING) is True

def test_log_level_from_string():
    """Test string to LogLevel conversion."""
    assert LogLevel.from_string("debug") == LogLevel.DEBUG
    assert LogLevel.from_string("INFO") == LogLevel.INFO
    with pytest.raises(ValueError):
        LogLevel.from_string("invalid")

def test_log_config_defaults():
    """Test default configuration values."""
    config = LogConfig()
    assert config.level == LogLevel.INFO
    assert config.retention_days == 7
    assert config.max_file_size == 10 * 1024 * 1024
    assert config.backup_count == 5
    assert config.metrics_enabled is True
    assert config.discord_webhook is None

def test_log_config_serialization(tmp_path):
    """Test config serialization to/from JSON."""
    config = LogConfig(
        level=LogLevel.DEBUG,
        retention_days=14,
        metrics_enabled=False
    )
    
    # Save config
    config_path = tmp_path / "log_config.json"
    config.save(str(config_path))
    
    # Load config
    loaded_config = LogConfig.load(str(config_path))
    assert loaded_config.level == LogLevel.DEBUG
    assert loaded_config.retention_days == 14
    assert loaded_config.metrics_enabled is False

def test_path_helpers():
    """Test path helper functions."""
    cwd = os.getcwd()
    assert get_log_path() == os.path.join(cwd, "logs")
    assert get_metrics_path() == os.path.join(cwd, "logs", "metrics")

def test_retention_date():
    """Test retention date calculation."""
    retention_date = get_retention_date()
    expected_date = datetime.now() - timedelta(days=DEFAULT_CONFIG.retention_days)
    # Allow 1 second difference for test execution time
    assert abs((retention_date - expected_date).total_seconds()) < 1 
