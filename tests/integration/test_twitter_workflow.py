"""
Integration tests for the Twitter workflow.
Tests the entire pipeline from content scheduling to audience analytics.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from social.community.content_scheduler import ContentScheduler
from social.community.audience_analytics import AudienceAnalytics

@pytest.fixture
def mock_twitter_api():
    """Mock Twitter API client."""
    mock = MagicMock()
    mock.post_tweet.return_value = {"id": "123456", "text": "Test tweet"}
    mock.get_user_metrics.return_value = {
        "followers_count": 1000,
        "following_count": 500,
        "tweet_count": 100
    }
    mock.get_engagement_metrics.return_value = {
        "likes": 50,
        "retweets": 25,
        "replies": 10
    }
    return mock

@pytest.fixture
def twitter_workflow(temp_config_dir, temp_log_dir, mock_twitter_api):
    """Set up the complete Twitter workflow with mocked dependencies."""
    scheduler = ContentScheduler(str(temp_config_dir), str(temp_log_dir))
    analytics = AudienceAnalytics(str(temp_config_dir), str(temp_log_dir))
    
    # Patch the Twitter API client
    with patch('social.community.content_scheduler.TwitterAPI', return_value=mock_twitter_api), \
         patch('social.community.audience_analytics.TwitterAPI', return_value=mock_twitter_api):
        yield {
            'scheduler': scheduler,
            'analytics': analytics,
            'api': mock_twitter_api
        }

@pytest.mark.asyncio
async def test_twitter_content_scheduling(twitter_workflow):
    """Test the content scheduling workflow for Twitter."""
    scheduler = twitter_workflow['scheduler']
    api = twitter_workflow['api']
    
    # Test content scheduling
    content = {
        "text": "Test tweet content",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Schedule the post
    result = scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert result is True
    
    # Verify post was scheduled
    scheduled_posts = scheduler.get_schedule("twitter")
    assert len(scheduled_posts) == 1
    assert scheduled_posts[0]["content"] == content
    assert scheduled_posts[0]["platform"] == "twitter"
    
    # Test optimization
    optimization_result = scheduler.optimize_timing("twitter")
    assert optimization_result["platform"] == "twitter"
    assert "optimization_score" in optimization_result
    assert "recommended_times" in optimization_result

@pytest.mark.asyncio
async def test_twitter_audience_analytics(twitter_workflow):
    """Test the audience analytics workflow for Twitter."""
    analytics = twitter_workflow['analytics']
    api = twitter_workflow['api']
    
    # Test growth tracking
    metrics = {
        "followers": 1000,
        "following": 500,
        "posts": 100
    }
    growth_result = analytics.track_growth("twitter", metrics)
    assert growth_result["platform"] == "twitter"
    assert "growth_rate" in growth_result
    
    # Test demographics analysis
    demographics = {
        "age_groups": {"18-24": 30, "25-34": 40, "35-44": 20, "45+": 10},
        "locations": {"US": 60, "UK": 20, "Other": 20},
        "interests": ["tech", "science", "AI"]
    }
    demo_result = analytics.analyze_demographics("twitter", demographics)
    assert demo_result["platform"] == "twitter"
    assert "demographics" in demo_result
    assert "insights" in demo_result

@pytest.mark.asyncio
async def test_twitter_end_to_end_workflow(twitter_workflow):
    """Test the complete Twitter workflow from scheduling to analytics."""
    scheduler = twitter_workflow['scheduler']
    analytics = twitter_workflow['analytics']
    api = twitter_workflow['api']
    
    # 1. Schedule content
    content = {
        "text": "End-to-end test tweet",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    
    # 2. Get optimal posting time
    optimization = scheduler.optimize_timing("twitter")
    assert optimization["platform"] == "twitter"
    
    # 3. Track audience growth
    metrics = {
        "followers": 1000,
        "following": 500,
        "posts": 100
    }
    growth = analytics.track_growth("twitter", metrics)
    
    # 4. Analyze demographics
    demographics = {
        "age_groups": {"18-24": 30, "25-34": 40, "35-44": 20, "45+": 10},
        "locations": {"US": 60, "UK": 20, "Other": 20},
        "interests": ["tech", "science", "AI"]
    }
    analytics.analyze_demographics("twitter", demographics)
    
    # 5. Generate insights
    insights = analytics.generate_insights("twitter", {
        "engagement": {"likes": 1000, "retweets": 500, "replies": 200},
        "content": {"text": 70, "images": 20, "videos": 10},
        "timing": {"morning": 40, "afternoon": 35, "evening": 25}
    })
    assert "insights" in insights
    assert "recommendations" in insights
    
    # 6. Export report
    report = analytics.export_report("twitter", "growth", "json")
    assert report["platform"] == "twitter"
    assert report["type"] == "growth"
    assert "data" in report

@pytest.mark.asyncio
async def test_twitter_network_failure_recovery(twitter_workflow):
    """Test recovery from network failures during post scheduling."""
    scheduler = twitter_workflow['scheduler']
    api = twitter_workflow['api']
    
    # Simulate network failure
    api.post_tweet.side_effect = Exception("Network error")
    
    content = {
        "text": "Test tweet content",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule post
    with pytest.raises(Exception) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Network error" in str(exc_info.value)
    
    # Reset mock to simulate recovery
    api.post_tweet.side_effect = None
    api.post_tweet.return_value = {"id": "123456", "text": "Test tweet"}
    
    # Retry scheduling
    result = scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert result is True
    
    # Verify post was scheduled after recovery
    scheduled_posts = scheduler.get_schedule("twitter")
    assert len(scheduled_posts) == 1
    assert scheduled_posts[0]["content"] == content

@pytest.mark.asyncio
async def test_twitter_rate_limit_handling(twitter_workflow):
    """Test handling of Twitter API rate limits."""
    scheduler = twitter_workflow['scheduler']
    api = twitter_workflow['api']
    
    # Simulate rate limit error
    api.post_tweet.side_effect = Exception("Rate limit exceeded")
    
    content = {
        "text": "Test tweet content",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule post
    with pytest.raises(Exception) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Rate limit exceeded" in str(exc_info.value)
    
    # Verify rate limit handling in logs
    assert any("Rate limit exceeded" in record.message 
              for record in scheduler.logger.handlers[0].records)

@pytest.mark.asyncio
async def test_twitter_media_upload_failure(twitter_workflow):
    """Test handling of media upload failures."""
    scheduler = twitter_workflow['scheduler']
    api = twitter_workflow['api']
    
    # Simulate media upload failure
    api.upload_media.side_effect = Exception("Media upload failed")
    
    content = {
        "text": "Test tweet with media",
        "media": ["test_image.jpg"],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule post with media
    with pytest.raises(Exception) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Media upload failed" in str(exc_info.value)
    
    # Verify media upload failure handling
    assert any("Media upload failed" in record.message 
              for record in scheduler.logger.handlers[0].records)

@pytest.mark.asyncio
async def test_twitter_analytics_failure_recovery(twitter_workflow):
    """Test recovery from analytics data retrieval failures."""
    analytics = twitter_workflow['analytics']
    api = twitter_workflow['api']
    
    # Simulate analytics API failure
    api.get_engagement_metrics.side_effect = Exception("Analytics API error")
    
    # Attempt to get engagement metrics
    with pytest.raises(Exception) as exc_info:
        analytics.track_growth("twitter", {"followers": 1000, "following": 500})
    assert "Analytics API error" in str(exc_info.value)
    
    # Reset mock to simulate recovery
    api.get_engagement_metrics.side_effect = None
    api.get_engagement_metrics.return_value = {
        "likes": 50,
        "retweets": 25,
        "replies": 10
    }
    
    # Retry analytics
    result = analytics.track_growth("twitter", {"followers": 1000, "following": 500})
    assert result["platform"] == "twitter"
    assert "growth_rate" in result

@pytest.mark.asyncio
async def test_twitter_authentication_failure(twitter_workflow):
    """Test handling of authentication failures."""
    scheduler = twitter_workflow['scheduler']
    api = twitter_workflow['api']
    
    # Simulate authentication failure
    api.post_tweet.side_effect = Exception("Authentication failed")
    
    content = {
        "text": "Test tweet content",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule post
    with pytest.raises(Exception) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Authentication failed" in str(exc_info.value)
    
    # Verify authentication failure handling
    assert any("Authentication failed" in record.message 
              for record in scheduler.logger.handlers[0].records)

@pytest.mark.asyncio
async def test_twitter_content_validation_failure(twitter_workflow):
    """Test handling of content validation failures."""
    scheduler = twitter_workflow['scheduler']
    
    # Test with invalid content (empty text)
    content = {
        "text": "",
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule invalid post
    with pytest.raises(ValueError) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Invalid content" in str(exc_info.value)
    
    # Test with content exceeding length limit
    content = {
        "text": "x" * 281,  # Exceeds Twitter's 280 character limit
        "media": [],
        "scheduled_time": datetime.now() + timedelta(hours=1)
    }
    
    # Attempt to schedule oversized post
    with pytest.raises(ValueError) as exc_info:
        scheduler.schedule_post(content, "twitter", content["scheduled_time"])
    assert "Content too long" in str(exc_info.value) 