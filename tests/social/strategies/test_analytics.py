import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

class AnalyticsManager:
    """Analytics management system for social media content."""
    
    def __init__(self, platform: str):
        """
        Initialize analytics manager for a specific platform.
        
        Args:
            platform: The social media platform (e.g., 'twitter', 'facebook')
        """
        self.platform = platform
        self.metrics: Dict[int, Dict[str, Any]] = {}  # content_id -> metrics
        self.engagement_history: List[Dict[str, Any]] = []
        
    def track_engagement(self, content_id: int, engagement_type: str, count: int = 1) -> None:
        """
        Track engagement metrics for content.
        
        Args:
            content_id: ID of the content
            engagement_type: Type of engagement (e.g., 'likes', 'comments', 'shares')
            count: Number of engagements (default: 1)
        """
        if content_id not in self.metrics:
            self.metrics[content_id] = {
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'views': 0,
                'last_updated': datetime.now()
            }
            
        if engagement_type not in self.metrics[content_id]:
            raise ValueError(f"Invalid engagement type: {engagement_type}")
            
        self.metrics[content_id][engagement_type] += count
        self.metrics[content_id]['last_updated'] = datetime.now()
        
        self.engagement_history.append({
            'content_id': content_id,
            'type': engagement_type,
            'count': count,
            'timestamp': datetime.now()
        })
    
    def get_content_metrics(self, content_id: int) -> Dict[str, Any]:
        """
        Get metrics for specific content.
        
        Args:
            content_id: ID of the content
            
        Returns:
            Dict containing content metrics
        """
        if content_id not in self.metrics:
            raise ValueError(f"No metrics found for content {content_id}")
            
        return self.metrics[content_id]
    
    def get_platform_metrics(self, start_time: Optional[datetime] = None, 
                           end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get aggregated metrics for the platform.
        
        Args:
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            
        Returns:
            Dict containing aggregated metrics
        """
        if not start_time:
            start_time = datetime.now() - timedelta(days=30)
        if not end_time:
            end_time = datetime.now()
            
        filtered_history = [
            entry for entry in self.engagement_history
            if start_time <= entry['timestamp'] <= end_time
        ]
        
        metrics = {
            'total_engagements': 0,
            'engagement_by_type': {
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'views': 0
            },
            'top_content': [],
            'engagement_trend': []
        }
        
        # Aggregate metrics
        for entry in filtered_history:
            if entry['type'] != 'views':  # Exclude views from total engagements
                metrics['total_engagements'] += entry['count']
            metrics['engagement_by_type'][entry['type']] += entry['count']
            
        # Calculate top content
        content_metrics = {}
        for entry in filtered_history:
            if entry['type'] != 'views':  # Exclude views from content ranking
                if entry['content_id'] not in content_metrics:
                    content_metrics[entry['content_id']] = 0
                content_metrics[entry['content_id']] += entry['count']
            
        metrics['top_content'] = sorted(
            [(cid, score) for cid, score in content_metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return metrics
    
    def calculate_engagement_rate(self, content_id: int) -> float:
        """
        Calculate engagement rate for content.
        
        Args:
            content_id: ID of the content
            
        Returns:
            float: Engagement rate (engagements / views)
        """
        if content_id not in self.metrics:
            raise ValueError(f"No metrics found for content {content_id}")
            
        metrics = self.metrics[content_id]
        views = metrics['views']
        
        if views == 0:
            return 0.0
            
        engagements = sum(
            metrics[type_] for type_ in ['likes', 'comments', 'shares']
        )
        
        return engagements / views

class TestAnalyticsManager:
    """Test suite for analytics management system."""
    
    @pytest.fixture
    def analytics_manager(self):
        """Fixture providing an analytics manager instance."""
        return AnalyticsManager('twitter')
    
    def test_engagement_tracking(self, analytics_manager):
        """Test engagement tracking functionality."""
        # Track initial engagement
        analytics_manager.track_engagement(1, 'likes', 5)
        analytics_manager.track_engagement(1, 'comments', 2)
        
        metrics = analytics_manager.get_content_metrics(1)
        assert metrics['likes'] == 5
        assert metrics['comments'] == 2
        assert metrics['shares'] == 0
        
        # Test invalid engagement type
        with pytest.raises(ValueError):
            analytics_manager.track_engagement(1, 'invalid_type')
    
    def test_content_metrics(self, analytics_manager):
        """Test content metrics retrieval."""
        # Set up test data
        analytics_manager.track_engagement(1, 'likes', 10)
        analytics_manager.track_engagement(1, 'views', 100)
        
        # Test metrics retrieval
        metrics = analytics_manager.get_content_metrics(1)
        assert metrics['likes'] == 10
        assert metrics['views'] == 100
        
        # Test non-existent content
        with pytest.raises(ValueError):
            analytics_manager.get_content_metrics(999)
    
    def test_platform_metrics(self, analytics_manager):
        """Test platform-wide metrics aggregation."""
        # Set up test data across multiple content items
        analytics_manager.track_engagement(1, 'likes', 10)
        analytics_manager.track_engagement(1, 'views', 100)
        analytics_manager.track_engagement(2, 'likes', 20)
        analytics_manager.track_engagement(2, 'views', 200)
        
        # Test metrics aggregation
        metrics = analytics_manager.get_platform_metrics()
        assert metrics['total_engagements'] == 30
        assert metrics['engagement_by_type']['likes'] == 30
        assert len(metrics['top_content']) <= 5
        
        # Test time range filtering
        past_time = datetime.now() - timedelta(days=1)
        future_time = datetime.now() + timedelta(days=1)
        filtered_metrics = analytics_manager.get_platform_metrics(past_time, future_time)
        assert filtered_metrics['total_engagements'] == 30
    
    def test_engagement_rate(self, analytics_manager):
        """Test engagement rate calculation."""
        # Set up test data
        analytics_manager.track_engagement(1, 'likes', 10)
        analytics_manager.track_engagement(1, 'comments', 5)
        analytics_manager.track_engagement(1, 'views', 100)
        
        # Test engagement rate calculation
        rate = analytics_manager.calculate_engagement_rate(1)
        assert rate == 0.15  # (10 + 5) / 100
        
        # Test zero views
        analytics_manager.track_engagement(2, 'likes', 5)
        rate = analytics_manager.calculate_engagement_rate(2)
        assert rate == 0.0
        
        # Test non-existent content
        with pytest.raises(ValueError):
            analytics_manager.calculate_engagement_rate(999) 
