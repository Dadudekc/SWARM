from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import os

@dataclass
class RedditConfig:
    """Reddit-specific configuration."""
    username: str
    password: str
    cookies_path: Path
    max_retries: int = 3
    retry_delay: int = 2
    session_timeout: int = 24  # hours
    rate_limit_posts: int = 10  # posts per hour
    rate_limit_comments: int = 50  # comments per hour
    supported_image_formats: list = None
    supported_video_formats: list = None
    max_images: int = 20
    max_videos: int = 1
    max_video_size: int = 100 * 1024 * 1024  # 100MB

    def __post_init__(self):
        """Initialize default values."""
        if self.supported_image_formats is None:
            self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        if self.supported_video_formats is None:
            self.supported_video_formats = [".mp4", ".mov", ".avi"]
        
        # Ensure cookies_path is a Path object
        if isinstance(self.cookies_path, str):
            self.cookies_path = Path(self.cookies_path)
        
        # Create cookies directory if it doesn't exist
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'RedditConfig':
        """Create config from dictionary."""
        required_fields = ['username', 'password', 'cookies_path']
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
        
        return cls(**config)

    @classmethod
    def load(cls, config_path: str) -> 'RedditConfig':
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return cls.from_dict(config)
        except Exception as e:
            raise ValueError(f"Failed to load Reddit configuration: {str(e)}")

    def save(self, config_path: str) -> None:
        """Save configuration to file."""
        try:
            config_dict = {
                'username': self.username,
                'password': self.password,
                'cookies_path': str(self.cookies_path),
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'session_timeout': self.session_timeout,
                'rate_limit_posts': self.rate_limit_posts,
                'rate_limit_comments': self.rate_limit_comments,
                'supported_image_formats': self.supported_image_formats,
                'supported_video_formats': self.supported_video_formats,
                'max_images': self.max_images,
                'max_videos': self.max_videos,
                'max_video_size': self.max_video_size
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            raise ValueError(f"Failed to save Reddit configuration: {str(e)}")

    def validate(self) -> bool:
        """Validate configuration values."""
        try:
            # Check required fields
            if not self.username or not self.password:
                return False
            
            # Check paths
            if not self.cookies_path:
                return False
            
            # Check numeric values
            if self.max_retries < 1 or self.retry_delay < 1:
                return False
            if self.session_timeout < 1:
                return False
            if self.rate_limit_posts < 1 or self.rate_limit_comments < 1:
                return False
            if self.max_images < 1 or self.max_videos < 1:
                return False
            if self.max_video_size < 1024 * 1024:  # At least 1MB
                return False
            
            # Check file formats
            if not self.supported_image_formats or not self.supported_video_formats:
                return False
            
            return True
        except Exception:
            return False 
