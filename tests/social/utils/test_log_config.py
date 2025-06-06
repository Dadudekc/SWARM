"""
Test suite for LogConfig functionality.
"""

import pytest
from pathlib import Path
from dreamos.core.logging.log_config import LogConfig, LogLevel
import tempfile
import os
from datetime import datetime

def test_config_initialization():
    """Test configuration initialization with custom values."""
    config = LogConfig(
        level=LogLevel.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        retention_days=30,
        max_file_size=20 * 1024 * 1024,  # 20MB
        backup_count=5,
        metrics_enabled=True,
        log_dir="custom_logs",
        platforms={"test": "test.log"}
    )
    assert config.level == LogLevel.INFO
    assert str(Path(config.log_dir).resolve()) == str(Path("custom_logs").resolve())
    assert config.max_file_size == 20 * 1024 * 1024
    assert config.platforms == {"test": "test.log"}

def test_config_defaults():
    """Test default configuration values."""
    config = LogConfig()
    assert config.level == LogLevel.INFO
    assert config.format == "[{timestamp}] [{level}] {message}"
    assert config.retention_days == 7
    assert config.max_file_size == 10 * 1024 * 1024  # 10MB
    assert config.backup_count == 5
    assert config.metrics_enabled is True
    assert config.log_dir is None
    assert config.platforms is None

def test_config_custom_values():
    """Test LogConfig with custom values."""
    config = LogConfig(
        level=LogLevel.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        retention_days=30,
        max_file_size=20 * 1024 * 1024,  # 20MB
        backup_count=5,
        metrics_enabled=True,
        log_dir="custom_logs",
        platforms={"test": "test.log"},
        batch_size=10,
        batch_timeout=1.0,
        max_retries=3,
        retry_delay=0.5
    )
    assert str(Path(config.log_dir).resolve()) == str(Path("custom_logs").resolve())
    assert config.level == LogLevel.DEBUG
    assert config.max_file_size == 20 * 1024 * 1024
    assert config.batch_size == 10
    assert config.batch_timeout == 1.0
    assert config.max_retries == 3
    assert config.retry_delay == 0.5

def test_config_invalid_level():
    """Test LogConfig with invalid level."""
    with pytest.raises(ValueError):
        LogConfig(level="INVALID")

def test_config_platforms():
    """Test LogConfig platform settings."""
    config = LogConfig(platforms={"test": "test.log"})
    assert "test" in config.platforms
    assert str(Path(config.platforms["test"]).resolve()) == str(Path("test.log").resolve())

def test_log_dir_creation(tmp_path):
    """Test log directory creation."""
    cfg = LogConfig(log_dir=str(tmp_path))
    expected_dir = cfg.log_dir  # use runtime config
    assert Path(expected_dir).exists()

def test_platform_paths():
    """Test platform log file paths."""
    config = LogConfig(platforms={"test": "test.log"})
    assert Path(config.platforms["test"]).resolve() == Path("test.log").resolve()

class TestLogConfig:
    """Test suite for LogConfig class."""
    
    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create a temporary log directory."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return log_dir
        
    @pytest.fixture
    def default_config(self, temp_log_dir):
        """Create a default LogConfig instance."""
        return LogConfig(log_dir=str(temp_log_dir))
        
    def test_default_initialization(self, temp_log_dir):
        """Test default initialization with minimal parameters."""
        config = LogConfig(log_dir=str(temp_log_dir))
        
        assert config.log_dir == str(temp_log_dir)
        assert config.level == LogLevel.INFO
        assert config.format == "[{timestamp}] [{level}] {message}"
        assert config.retention_days == 7
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.backup_count == 5
        assert config.metrics_enabled is True
        assert config.platforms is None
        
    def test_custom_initialization(self, temp_log_dir):
        """Test initialization with custom parameters."""
        config = LogConfig(
            level=LogLevel.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            retention_days=30,
            max_file_size=20 * 1024 * 1024,  # 20MB
            backup_count=5,
            metrics_enabled=True,
            log_dir=str(temp_log_dir),
            platforms={"test": "test.log"},
            batch_size=10,
            batch_timeout=1.0,
            max_retries=3,
            retry_delay=0.5
        )
        
        assert config.log_dir == str(temp_log_dir)
        assert config.level == LogLevel.DEBUG
        assert config.max_file_size == 20 * 1024 * 1024
        assert config.batch_size == 10
        assert config.batch_timeout == 1.0
        assert config.max_retries == 3
        assert config.retry_delay == 0.5
        
    def test_invalid_log_dir(self):
        """Test initialization with invalid log directory."""
        with pytest.raises(ValueError):
            LogConfig(log_dir="/nonexistent/path")
            
    def test_invalid_batch_size(self, temp_log_dir):
        """Test initialization with invalid batch size."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), batch_size=0)
            
    def test_invalid_timeout(self, temp_log_dir):
        """Test initialization with invalid timeout."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), batch_timeout=-1)
            
    def test_invalid_retries(self, temp_log_dir):
        """Test initialization with invalid retry count."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), max_retries=-1)
            
    def test_invalid_retry_delay(self, temp_log_dir):
        """Test initialization with invalid retry delay."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), retry_delay=-1)
            
    def test_invalid_max_size(self, temp_log_dir):
        """Test initialization with invalid max size."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), max_file_size=0)
            
    def test_invalid_max_files(self, temp_log_dir):
        """Test initialization with invalid max files."""
        with pytest.raises(ValueError):
            LogConfig(log_dir=str(temp_log_dir), backup_count=0)
            
    def test_config_serialization(self, temp_log_dir):
        """Test config serialization to dictionary."""
        original_config = LogConfig(
            level=LogLevel.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            retention_days=30,
            max_file_size=20 * 1024 * 1024,  # 20MB
            backup_count=5,
            metrics_enabled=True,
            log_dir=str(temp_log_dir),
            platforms={"test": "test.log"},
            batch_size=10,
            batch_timeout=1.0,
            max_retries=3,
            retry_delay=0.5
        )
        
        config_dict = original_config.to_dict()
        restored_config = LogConfig.from_dict(config_dict)
        
        assert restored_config.level == original_config.level
        assert restored_config.format == original_config.format
        assert restored_config.retention_days == original_config.retention_days
        assert restored_config.max_file_size == original_config.max_file_size
        assert restored_config.backup_count == original_config.backup_count
        assert restored_config.metrics_enabled == original_config.metrics_enabled
        assert restored_config.log_dir == original_config.log_dir
        assert restored_config.platforms == original_config.platforms
        assert restored_config.batch_size == original_config.batch_size
        assert restored_config.batch_timeout == original_config.batch_timeout
        assert restored_config.max_retries == original_config.max_retries
        assert restored_config.retry_delay == original_config.retry_delay 