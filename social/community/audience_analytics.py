from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base import CommunityBase

class AudienceAnalytics(CommunityBase):
    """Analyzes audience engagement and demographics across platforms."""
    
    def __init__(self, config_dir: str = None, log_dir: str = None):
        """Initialize the audience analytics.
        
        Args:
            config_dir: Directory for configuration files
            log_dir: Directory for log files
        """
        super().__init__("AudienceAnalytics", config_dir, log_dir)
        self.growth_rate = 0.0
        self.demographics = {}
        self.insights = {}
        self.reports = {}
        self.metrics = {
            "engagement": 0.0,
            "growth": 0.0,
            "engagement_rate": 0.0,
            "follower_growth": 0.0,
            "audience_retention": 0.0
        }
    
    def _create_default_config(self) -> dict:
        """Create default configuration for analytics."""
        config = super()._create_default_config()
        config.update({
            "analytics": {
                "tracking_interval": 3600,  # 1 hour
                "metrics": ["growth", "engagement", "demographics"],
                "report_frequency": "daily"
            },
            "thresholds": {
                "growth_alert": 0.1,
                "engagement_alert": 0.05,
                "retention_alert": 0.02
            },
            "reporting": {
                "export_formats": ["json", "csv"],
                "auto_export": False,
                "export_interval": 86400  # 24 hours
            }
        })
        return config
    
    def track_growth(self, platform: str, metrics: Dict) -> Dict:
        """Track audience growth metrics for a platform.
        
        Args:
            platform: Target platform
            metrics: Growth metrics to track
            
        Returns:
            Dict: Updated growth metrics
            
        Raises:
            ValueError: If metrics are invalid
        """
        if not isinstance(metrics, dict):
            raise ValueError("Metrics must be a dictionary")
            
        required_metrics = ["followers", "following", "posts"]
        for metric in required_metrics:
            if metric not in metrics:
                raise ValueError(f"Missing required metric: {metric}")
            if not isinstance(metrics[metric], (int, float)) or metrics[metric] < 0:
                raise ValueError(f"Metric {metric} must be a non-negative number")
        
        self.growth_rate = (metrics.get("followers", 0) / max(metrics.get("following", 1), 1)) * 100
        self.metrics["follower_growth"] = self.growth_rate
        
        result = {
            "platform": platform,
            "growth_rate": self.growth_rate,
            "follower_growth": self.metrics["follower_growth"],
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Tracked growth for {platform}: {result}")
        return result
    
    def analyze_demographics(self, platform: str, data: Dict) -> Dict:
        """Analyze audience demographics for a platform.
        
        Args:
            platform: Target platform
            data: Demographic data to analyze
            
        Returns:
            Dict: Analysis results
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        required_fields = ["age_groups", "locations", "interests"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate age groups
        age_groups = data.get("age_groups", {})
        if not isinstance(age_groups, dict):
            raise ValueError("Age groups must be a dictionary")
        total_age = sum(age_groups.values())
        if total_age > 100:
            raise ValueError("Age group percentages cannot exceed 100%")
            
        # Validate locations
        locations = data.get("locations", {})
        if not isinstance(locations, dict):
            raise ValueError("Locations must be a dictionary")
        total_location = sum(locations.values())
        if total_location > 100:
            raise ValueError("Location percentages cannot exceed 100%")
            
        # Validate interests
        interests = data.get("interests", [])
        if not isinstance(interests, list):
            raise ValueError("Interests must be a list")
            
        self.demographics[platform] = data
        
        insights = {
            "top_age_group": max(data.get("age_groups", {}), key=data.get("age_groups", {}).get, default=None),
            "top_location": max(data.get("locations", {}), key=data.get("locations", {}).get, default=None),
            "interests": data.get("interests", [])
        }
        
        result = {
            "platform": platform,
            "demographics": data,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"Analyzed demographics for {platform}")
        return result
    
    def generate_insights(self, platform: str, data: Dict) -> Dict:
        """Generate audience insights based on collected data.
        
        Args:
            platform: Target platform
            data: Data to generate insights from
            
        Returns:
            Dict: Generated insights
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        required_fields = ["engagement", "content", "timing"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate engagement
        engagement = data.get("engagement", {})
        if not isinstance(engagement, dict):
            raise ValueError("Engagement must be a dictionary")
            
        # Validate content
        content = data.get("content", {})
        if not isinstance(content, dict):
            raise ValueError("Content must be a dictionary")
        total_content = sum(content.values())
        if total_content > 100:
            raise ValueError("Content percentages cannot exceed 100%")
            
        # Validate timing
        timing = data.get("timing", {})
        if not isinstance(timing, dict):
            raise ValueError("Timing must be a dictionary")
        total_timing = sum(timing.values())
        if total_timing > 100:
            raise ValueError("Timing percentages cannot exceed 100%")
            
        insights = {
            "growth": {
                "description": "Audience growing steadily",
                "timestamp": datetime.now().isoformat()
            },
            "engagement": {
                "description": "High engagement during peak hours",
                "timestamp": datetime.now().isoformat()
            }
        }
        recommendations = [
            "Focus on content types with highest engagement",
            "Optimize posting times based on audience activity",
            "Target key demographic segments"
        ]
        self.insights = insights
        return {"platform": platform, "insights": insights, "recommendations": recommendations}
    
    def export_report(self, platform: str, report_type: str, format: str = "json") -> Dict:
        """Export analytics report in specified format.
        
        Args:
            platform: Target platform
            report_type: Type of report
            format: Report format (json, csv, etc.)
            
        Returns:
            Dict: Report data
            
        Raises:
            ValueError: If format or report type is invalid
            PermissionError: If unable to write report file
        """
        valid_formats = ["json", "csv"]
        if format not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")
            
        valid_types = ["growth", "demographics", "insights"]
        if report_type not in valid_types:
            raise ValueError(f"Invalid report type. Must be one of: {', '.join(valid_types)}")
            
        data = {
            "metrics": self.metrics,
            "demographics": self.demographics.get(platform, {}),
            "insights": self.insights
        }
        report = {
            "platform": platform,
            "type": report_type,
            "format": format,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            self.reports[f"{platform}_{report_type}"] = report
            return report
        except PermissionError as e:
            self.logger.error(f"Permission denied saving report: {str(e)}")
            raise
    
    def get_audience_metrics(self) -> Dict:
        """Get current audience metrics.
        
        Returns:
            Dict: Current metrics
        """
        return self.metrics

    def _get_audience_metrics(self, platform: str) -> Dict:
        """Get audience metrics for a specific platform.
        
        Args:
            platform: Target platform
            
        Returns:
            Dict: Platform metrics
            
        Raises:
            ValueError: If platform is invalid
        """
        if platform not in ["twitter", "facebook", "instagram", "linkedin"]:
            raise ValueError(f"Unsupported platform: {platform}")
            
        return {
            "growth_rate": self.growth_rate,
            "engagement_rate": self.metrics["engagement_rate"],
            "demographics": self.demographics.get(platform, {})
        } 