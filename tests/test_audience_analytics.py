import pytest
from datetime import datetime, timedelta
from social.community.audience_analytics import AudienceAnalytics
import logging

@pytest.fixture
def analytics_instance(temp_config_dir, temp_log_dir, monkeypatch):
    """Create an AudienceAnalytics instance with temporary directories."""
    # Patch the config and log paths
    monkeypatch.setattr(AudienceAnalytics, "_setup_logging", lambda self: None)
    config_path = temp_config_dir / "analytics_config.json"
    instance = AudienceAnalytics(str(config_path))
    instance.logger = logging.getLogger(instance.module_name)  # Ensure logger is set
    return instance

def test_init(analytics_instance):
    """Test initialization of AudienceAnalytics."""
    assert analytics_instance.growth_rate == 0.0
    assert isinstance(analytics_instance.demographics, dict)
    assert isinstance(analytics_instance.insights, dict)
    assert isinstance(analytics_instance.reports, dict)
    assert isinstance(analytics_instance.metrics, dict)
    assert "engagement" in analytics_instance.metrics
    assert analytics_instance.metrics["engagement"] == 0.0

def test_create_default_config(analytics_instance):
    """Test default configuration creation."""
    config = analytics_instance._create_default_config()
    assert "analytics" in config
    assert "reporting" in config
    assert config["analytics"]["tracking_interval"] == 3600
    assert config["analytics"]["metrics"] == ["growth", "engagement", "demographics"]
    assert config["reporting"]["export_formats"] == ["json", "csv"]

def test_track_growth(analytics_instance):
    """Test growth tracking."""
    platform = "twitter"
    metrics = {
        "followers": 1000,
        "following": 500,
        "posts": 50
    }
    
    result = analytics_instance.track_growth(platform, metrics)
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert "growth_rate" in result
    assert "metrics" in result
    assert result["metrics"] == metrics

def test_analyze_demographics(analytics_instance):
    """Test demographics analysis."""
    platform = "twitter"
    data = {
        "age_groups": {"18-24": 30, "25-34": 40, "35-44": 20, "45+": 10},
        "locations": {"US": 60, "UK": 20, "Other": 20},
        "interests": ["tech", "science", "AI"]
    }
    
    result = analytics_instance.analyze_demographics(platform, data)
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert "demographics" in result
    assert result["demographics"] == data
    assert "insights" in result

def test_generate_insights(analytics_instance):
    """Test insight generation."""
    platform = "twitter"
    data = {
        "engagement": {"likes": 1000, "retweets": 500, "replies": 200},
        "content": {"text": 70, "images": 20, "videos": 10},
        "timing": {"morning": 40, "afternoon": 35, "evening": 25}
    }
    
    result = analytics_instance.generate_insights(platform, data)
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert "insights" in result
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)

def test_export_report(analytics_instance):
    """Test report export."""
    platform = "twitter"
    report_type = "growth"
    format = "json"
    
    # First generate some data
    analytics_instance.track_growth(platform, {"followers": 1000, "following": 500})
    
    result = analytics_instance.export_report(platform, report_type, format)
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert result["type"] == report_type
    assert result["format"] == format
    assert "data" in result
    assert "timestamp" in result

def test_get_audience_metrics(analytics_instance):
    """Test audience metrics retrieval."""
    platform = "twitter"
    metrics = analytics_instance._get_audience_metrics(platform)
    
    assert isinstance(metrics, dict)
    assert "growth_rate" in metrics
    assert "engagement_rate" in metrics
    assert "demographics" in metrics 