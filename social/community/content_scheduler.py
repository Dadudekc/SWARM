from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base import CommunityBase

class ContentScheduler(CommunityBase):
    """Manages content scheduling and optimization across platforms."""
    
    SUPPORTED_PLATFORMS = ["twitter", "facebook", "instagram", "linkedin"]
    
    def __init__(self, config_dir: str = None, log_dir: str = None):
        """Initialize the content scheduler.
        
        Args:
            config_dir: Directory for configuration files
            log_dir: Directory for log files
        """
        super().__init__("ContentScheduler", config_dir, log_dir)
        self.scheduled_posts = []
        self.optimization_score = 0.0
        self.engagement_rate = 0.0
        self.best_posting_times = {}
        self.content_performance = {}
    
    def _create_default_config(self) -> dict:
        """Create default configuration for the scheduler."""
        config = super()._create_default_config()
        config.update({
            "scheduling": {
                "max_posts_per_day": 10,
                "min_time_between_posts": 60,  # minutes
                "timezone": "UTC"
            },
            "optimization": {
                "engagement_threshold": 0.5,
                "performance_metrics": ["likes", "shares", "comments"],
                "optimization_interval": 3600  # 1 hour
            }
        })
        return config
    
    def _validate_platform(self, platform: str) -> None:
        """Validate platform name.
        
        Args:
            platform: Platform to validate
            
        Raises:
            ValueError: If platform is not supported
        """
        if platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _validate_content(self, content: dict) -> None:
        """Validate post content.
        
        Args:
            content: Content to validate
            
        Raises:
            ValueError: If content is invalid
        """
        if not isinstance(content, dict):
            raise ValueError("Content must be a dictionary")
        if "text" not in content:
            raise ValueError("Content must include 'text' field")
    
    def _validate_scheduled_time(self, scheduled_time: datetime) -> None:
        """Validate scheduled time.
        
        Args:
            scheduled_time: Time to validate
            
        Raises:
            ValueError: If time is in the past
        """
        if scheduled_time < datetime.now():
            raise ValueError("Cannot schedule posts in the past")
    
    def _check_rate_limit(self, platform: str) -> None:
        """Check if platform has reached its daily post limit.
        
        Args:
            platform: Platform to check
            
        Raises:
            ValueError: If rate limit is exceeded
        """
        today_posts = [
            post for post in self.scheduled_posts
            if post["platform"] == platform
            and post["scheduled_time"].date() == datetime.now().date()
        ]
        if len(today_posts) >= self.config["scheduling"]["max_posts_per_day"]:
            raise ValueError(f"Daily post limit reached for {platform}")
    
    def schedule_post(self, content: Dict, platform: str, scheduled_time: Optional[datetime] = None) -> bool:
        """Schedule a post for a specific platform.
        
        Args:
            content: Post content
            platform: Target platform
            scheduled_time: Optional specific time to post
            
        Returns:
            bool: True if successfully scheduled
            
        Raises:
            ValueError: If content, platform, or scheduling time is invalid
        """
        self._validate_platform(platform)
        self._validate_content(content)
        
        if scheduled_time is None:
            scheduled_time = self._get_optimal_time(platform)
        else:
            self._validate_scheduled_time(scheduled_time)
        
        self._check_rate_limit(platform)
            
        post = {
            "content": content,
            "platform": platform,
            "scheduled_time": scheduled_time,
            "status": "scheduled",
            "created_at": datetime.now()
        }
        
        self.scheduled_posts.append(post)
        self.logger.info(f"Scheduled post for {platform} at {scheduled_time}")
        return True
    
    def get_schedule(self, platform: Optional[str] = None) -> List[Dict]:
        """Get scheduled posts, optionally filtered by platform.
        
        Args:
            platform: Optional platform to filter by
            
        Returns:
            List[Dict]: List of scheduled posts
            
        Raises:
            ValueError: If platform is invalid
        """
        if platform:
            self._validate_platform(platform)
            return [post for post in self.scheduled_posts if post["platform"] == platform]
        return self.scheduled_posts
    
    def optimize_timing(self, platform: str) -> Dict:
        """Optimize posting times for a platform.
        
        Args:
            platform: Target platform
            
        Returns:
            Dict: Optimization results
            
        Raises:
            ValueError: If platform is invalid
        """
        self._validate_platform(platform)
        
        # Placeholder for actual optimization logic
        recommended_times = [
            datetime.now() + timedelta(hours=i)
            for i in range(1, 4)
        ]
        
        result = {
            "platform": platform,
            "optimization_score": 0.8,
            "recommended_times": recommended_times
        }
        
        self.best_posting_times[platform] = recommended_times
        return result
    
    def analyze_performance(self) -> Dict:
        """Analyze content performance across platforms.
        
        Returns:
            Dict: Performance analysis results
        """
        # Placeholder for actual analysis logic
        result = {
            "optimization_score": self.optimization_score,
            "engagement_rate": self.engagement_rate,
            "content_performance": self.content_performance
        }
        return result
    
    def _get_optimal_time(self, platform: str) -> datetime:
        """Get optimal posting time for a platform.
        
        Args:
            platform: Target platform
            
        Returns:
            datetime: Optimal posting time
            
        Raises:
            ValueError: If platform is invalid
        """
        self._validate_platform(platform)
        # Placeholder for actual optimal time calculation
        return datetime.now() + timedelta(hours=1) 
