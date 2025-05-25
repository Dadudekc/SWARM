import pytest
from datetime import datetime, timedelta
from social.community.content_scheduler import ContentScheduler
import logging

@pytest.fixture
def scheduler_instance(temp_config_dir, temp_log_dir, monkeypatch):
    """Create a ContentScheduler instance with temporary directories."""
    # Patch the config and log paths
    monkeypatch.setattr(ContentScheduler, "_setup_logging", lambda self: None)
    config_path = temp_config_dir / "scheduler_config.json"
    instance = ContentScheduler(str(config_path))
    instance.logger = logging.getLogger(instance.module_name)  # Ensure logger is set
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

def test_optimize_timing(scheduler_instance):
    """Test timing optimization."""
    platform = "twitter"
    result = scheduler_instance.optimize_timing(platform)
    
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert "optimization_score" in result
    assert "recommended_times" in result
    assert isinstance(result["recommended_times"], list)

def test_analyze_performance(scheduler_instance):
    """Test performance analysis."""
    result = scheduler_instance.analyze_performance()
    
    assert isinstance(result, dict)
    assert "optimization_score" in result
    assert "engagement_rate" in result
    assert "content_performance" in result
    assert isinstance(result["content_performance"], dict)

def test_get_optimal_time(scheduler_instance):
    """Test optimal time calculation."""
    platform = "twitter"
    optimal_time = scheduler_instance._get_optimal_time(platform)
    
    assert isinstance(optimal_time, datetime)
    assert optimal_time > datetime.now() 