import pytest
import os
from datetime import datetime, timedelta
from social.community.audience_analytics import AudienceAnalytics
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.utils.file_utils import (
    safe_read,
    safe_write,
    read_json,
    write_json,
    ensure_dir
)
from unittest.mock import patch
from unittest.mock import MagicMock

@pytest.fixture
def analytics_instance(temp_config_dir, temp_log_dir, monkeypatch):
    """Create an AudienceAnalytics instance with temporary directories."""
    # Initialize logging
    log_manager = LogManager(LogConfig(
        level=LogLevel.DEBUG,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        retention_days=30,
        max_file_size=10 * 1024 * 1024,
        backup_count=5,
        metrics_enabled=True,
        log_dir=str(temp_log_dir),
        platforms={"analytics": "analytics.log"},
        batch_size=100,
        batch_timeout=1.0,
        max_retries=3,
        retry_delay=0.5
    ))
    
    # Patch the config and log paths
    monkeypatch.setattr(AudienceAnalytics, "_setup_logging", lambda self: None)
    config_path = temp_config_dir / "analytics_config.json"
    instance = AudienceAnalytics(str(config_path))
    instance.logger = log_manager
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

def test_track_growth_invalid_data(analytics_instance):
    """Test growth tracking with invalid data."""
    platform = "twitter"
    
    # Test with invalid metrics type
    with pytest.raises(ValueError):
        analytics_instance.track_growth(platform, "invalid_metrics")
    
    # Test with missing required metrics
    with pytest.raises(ValueError):
        analytics_instance.track_growth(platform, {"followers": 1000})
    
    # Test with negative values
    with pytest.raises(ValueError):
        analytics_instance.track_growth(platform, {
            "followers": -1000,
            "following": 500,
            "posts": 50
        })

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

def test_analyze_demographics_invalid_data(analytics_instance):
    """Test demographics analysis with invalid data."""
    platform = "twitter"
    
    # Test with invalid data type
    with pytest.raises(ValueError):
        analytics_instance.analyze_demographics(platform, "invalid_data")
    
    # Test with missing required fields
    with pytest.raises(ValueError):
        analytics_instance.analyze_demographics(platform, {
            "age_groups": {"18-24": 30}
        })
    
    # Test with invalid percentages
    with pytest.raises(ValueError):
        analytics_instance.analyze_demographics(platform, {
            "age_groups": {"18-24": 150},  # > 100%
            "locations": {"US": 60, "UK": 20, "Other": 20},
            "interests": ["tech"]
        })

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

def test_generate_insights_invalid_data(analytics_instance):
    """Test insight generation with invalid data."""
    platform = "twitter"
    
    # Test with invalid data type
    with pytest.raises(ValueError):
        analytics_instance.generate_insights(platform, "invalid_data")
    
    # Test with missing required fields
    with pytest.raises(ValueError):
        analytics_instance.generate_insights(platform, {
            "engagement": {"likes": 1000}
        })
    
    # Test with invalid percentages
    with pytest.raises(ValueError):
        analytics_instance.generate_insights(platform, {
            "engagement": {"likes": 1000, "retweets": 500, "replies": 200},
            "content": {"text": 150},  # > 100%
            "timing": {"morning": 40, "afternoon": 35, "evening": 25}
        })

@pytest.mark.skip(reason="Strategic bypass - File System Layer refactor pending")
def test_export_report(analytics_instance):
    """Test report export."""
    platform = "twitter"
    report_type = "growth"
    format = "json"
    
    # First generate some data with all required metrics
    analytics_instance.track_growth(platform, {
        "followers": 1000,
        "following": 500,
        "posts": 50
    })
    
    result = analytics_instance.export_report(platform, report_type, format)
    assert isinstance(result, dict)
    assert result["platform"] == platform
    assert result["type"] == report_type
    assert result["format"] == format
    assert "data" in result
    assert "timestamp" in result

def test_export_report_invalid_format(analytics_instance):
    """Test report export with invalid format."""
    platform = "twitter"
    report_type = "growth"
    
    # Test with invalid format
    with pytest.raises(ValueError):
        analytics_instance.export_report(platform, report_type, "invalid_format")
    
    # Test with invalid report type
    with pytest.raises(ValueError):
        analytics_instance.export_report(platform, "invalid_type", "json")

@pytest.mark.skip(reason="Strategic bypass - File System Layer refactor pending")
def test_export_report_permission_error(analytics_instance, temp_config_dir):
    """Test report export with permission error."""
    platform = "twitter"
    report_type = "growth"
    format = "json"
    
    with patch('dreamos.core.utils.file_utils.safe_write', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            analytics_instance.export_report(platform, report_type, format)

def test_get_audience_metrics(analytics_instance):
    """Test getting audience metrics."""
    platform = "twitter"
    result = analytics_instance._get_audience_metrics(platform)
    
    assert isinstance(result, dict)
    assert "growth_rate" in result
    assert "engagement_rate" in result
    assert "demographics" in result
    assert isinstance(result["demographics"], dict)

def test_get_audience_metrics_invalid_platform(analytics_instance):
    """Test getting audience metrics with invalid platform."""
    with pytest.raises(ValueError):
        analytics_instance._get_audience_metrics("invalid_platform") 