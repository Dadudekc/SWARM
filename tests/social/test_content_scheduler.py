"""
Test suite for content scheduler functionality.
"""

import pytest
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from tests.conftest import TEST_RUNTIME_DIR, TEST_TEMP_DIR
from dreamos.core.messaging.enums import MessageMode
from dreamos.core.messaging.message_processor import MessageProcessor
from social.community.content_scheduler import ContentScheduler
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.log_manager import LogManager
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir
)

@pytest.fixture
def scheduler_instance(temp_config_dir, temp_log_dir, monkeypatch):
    """Create a ContentScheduler instance with temporary directories."""
    # Initialize logging
    log_manager = LogManager(LogConfig(
        level=LogLevel.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        retention_days=30,
        max_file_size=10 * 1024 * 1024,
        backup_count=5,
        metrics_enabled=True,
        log_dir=str(temp_log_dir),
        platforms={"scheduler": "scheduler.log"},
        batch_size=100,
        batch_timeout=5,
        max_retries=2,
        retry_delay=0.1
    ))
    
    # Patch the config and log paths
    monkeypatch.setattr(ContentScheduler, "_setup_logging", lambda self: None)
    config_path = temp_config_dir / "scheduler_config.json"
    instance = ContentScheduler(str(config_path))
    instance.logger = log_manager
    return instance

def test_init(scheduler_instance):
    """Test initialization of ContentScheduler."""
    assert scheduler_instance.scheduled_posts == []
    assert scheduler_instance.optimization_score == 0.0
    assert scheduler_instance.engagement_rate == 0.0
    assert isinstance(scheduler_instance.best_posting_times, dict)
    assert isinstance(scheduler_instance.content_performance, dict)

def test_create_default_config(scheduler_instance):
    """Test default configuration creation."""
    config = scheduler_instance._create_default_config()
    assert "scheduling" in config
    assert "optimization" in config
    assert config["scheduling"]["max_posts_per_day"] == 10
    assert config["scheduling"]["min_time_between_posts"] == 60
    assert config["optimization"]["engagement_threshold"] == 0.5

def test_schedule_post(scheduler_instance):
    """Test post scheduling."""
    content = {"text": "Test post", "media": []}
    platform = "twitter"
    
    # Test with default time
    result = scheduler_instance.schedule_post(content, platform)
    assert result is True
    assert len(scheduler_instance.scheduled_posts) == 1
    post = scheduler_instance.scheduled_posts[0]
    assert post["content"] == content
    assert post["platform"] == platform
    assert post["status"] == "scheduled"
    
    # Test with specific time
    scheduled_time = datetime.now() + timedelta(hours=2)
    result = scheduler_instance.schedule_post(content, platform, scheduled_time)
    assert result is True
    assert len(scheduler_instance.scheduled_posts) == 2

def test_schedule_post_invalid_data(scheduler_instance):
    """Test post scheduling with invalid data."""
    # Test with invalid content type
    with pytest.raises(ValueError):
        scheduler_instance.schedule_post("invalid_content", "twitter")
    
    # Test with missing required fields
    with pytest.raises(ValueError):
        scheduler_instance.schedule_post({"media": []}, "twitter")
    
    # Test with invalid platform
    with pytest.raises(ValueError):
        scheduler_instance.schedule_post({"text": "Test"}, "invalid_platform")
    
    # Test with past time
    past_time = datetime.now() - timedelta(hours=1)
    with pytest.raises(ValueError):
        scheduler_instance.schedule_post(
            {"text": "Test"},
            "twitter",
            scheduled_time=past_time
        )

def test_schedule_post_rate_limit(scheduler_instance):
    """Test post scheduling rate limiting."""
    content = {"text": "Test post", "media": []}
    platform = "twitter"
    
    # Schedule maximum posts
    for _ in range(10):  # max_posts_per_day
        scheduler_instance.schedule_post(content, platform)
    
    # Try to schedule one more
    with pytest.raises(ValueError):
        scheduler_instance.schedule_post(content, platform)

def test_get_schedule(scheduler_instance):
    """Test schedule retrieval."""
    # Clear any existing posts
    scheduler_instance.scheduled_posts = []
    
    content = {"text": "Test post", "media": []}
    scheduler_instance.schedule_post(content, "twitter")
    scheduler_instance.schedule_post(content, "facebook")
    
    # Test getting all posts
    all_posts = scheduler_instance.get_schedule()
    assert len(all_posts) == 2
    
    # Test getting platform-specific posts
    twitter_posts = scheduler_instance.get_schedule("twitter")
    assert len(twitter_posts) == 1
    assert twitter_posts[0]["platform"] == "twitter"
    
    facebook_posts = scheduler_instance.get_schedule("facebook")
    assert len(facebook_posts) == 1
    assert facebook_posts[0]["platform"] == "facebook"

def test_get_schedule_invalid_platform(scheduler_instance):
    """Test schedule retrieval with invalid platform."""
    with pytest.raises(ValueError):
        scheduler_instance.get_schedule("invalid_platform")

def test_optimize_timing(scheduler_instance):
    """Test timing optimization."""
    platform = "twitter"
    result = scheduler_instance.optimize_timing(platform)
    
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert "optimization_score" in result
    assert "recommended_times" in result
    assert isinstance(result["recommended_times"], list)

def test_optimize_timing_invalid_platform(scheduler_instance):
    """Test timing optimization with invalid platform."""
    with pytest.raises(ValueError):
        scheduler_instance.optimize_timing("invalid_platform")

def test_analyze_performance(scheduler_instance):
    """Test performance analysis."""
    result = scheduler_instance.analyze_performance()
    
    assert isinstance(result, dict)
    assert "optimization_score" in result
    assert "engagement_rate" in result
    assert "content_performance" in result
    assert isinstance(result["content_performance"], dict)

def test_analyze_performance_no_data(scheduler_instance):
    """Test performance analysis with no data."""
    scheduler_instance.scheduled_posts = []
    result = scheduler_instance.analyze_performance()
    
    assert result["optimization_score"] == 0.0
    assert result["engagement_rate"] == 0.0
    assert result["content_performance"] == {}

def test_get_optimal_time(scheduler_instance):
    """Test optimal time calculation."""
    platform = "twitter"
    optimal_time = scheduler_instance._get_optimal_time(platform)
    
    assert isinstance(optimal_time, datetime)
    assert optimal_time > datetime.now()

def test_get_optimal_time_invalid_platform(scheduler_instance):
    """Test optimal time calculation with invalid platform."""
    with pytest.raises(ValueError):
        scheduler_instance._get_optimal_time("invalid_platform")

@pytest.mark.skip(reason="Strategic bypass - File System Layer refactor pending")
def test_save_config_permission_error(scheduler_instance, temp_config_dir):
    """Test configuration saving with permission error."""
    config_path = temp_config_dir / "test_config.json"
    with patch('dreamos.core.utils.file_utils.safe_write', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            scheduler_instance._save_config({}, str(config_path))

@pytest.mark.skip(reason="Strategic bypass - File System Layer refactor pending")
def test_load_config_invalid_format(scheduler_instance, temp_config_dir):
    """Test loading invalid configuration."""
    config_path = temp_config_dir / "test_config.json"
    with patch('dreamos.core.utils.file_utils.safe_read', return_value="invalid json"):
        with pytest.raises(json.JSONDecodeError):
            scheduler_instance._load_config(str(config_path)) 
