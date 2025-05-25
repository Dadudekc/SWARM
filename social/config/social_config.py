"""
Social Media Configuration
-------------------------
Central configuration for all social media platforms.
Store credentials, posting rules, and platform-specific settings.
"""

import os
from typing import Dict, Any

# Base configuration
social_config: Dict[str, Any] = {
    # Facebook Configuration
    "facebook": {
        "enabled": True,
        "email": os.getenv("FACEBOOK_EMAIL", ""),
        "password": os.getenv("FACEBOOK_PASSWORD", ""),
        "post_interval": 3600,  # seconds between posts
        "max_posts_per_day": 5,
        "hashtags": ["#DreamOS", "#AI", "#Automation"],
    },
    
    # Twitter Configuration
    "twitter": {
        "enabled": True,
        "email": os.getenv("TWITTER_EMAIL", ""),
        "password": os.getenv("TWITTER_PASSWORD", ""),
        "post_interval": 1800,  # seconds between posts
        "max_posts_per_day": 10,
        "hashtags": ["#DreamOS", "#AI", "#Automation"],
    },
    
    # Instagram Configuration
    "instagram": {
        "enabled": True,
        "username": os.getenv("INSTAGRAM_USERNAME", ""),
        "password": os.getenv("INSTAGRAM_PASSWORD", ""),
        "post_interval": 7200,  # seconds between posts
        "max_posts_per_day": 3,
        "hashtags": ["#DreamOS", "#AI", "#Automation"],
    },
    
    # Reddit Configuration
    "reddit": {
        "enabled": True,
        "username": os.getenv("REDDIT_USERNAME", ""),
        "password": os.getenv("REDDIT_PASSWORD", ""),
        "post_interval": 3600,  # seconds between posts
        "max_posts_per_day": 5,
        "subreddits": ["r/artificial", "r/programming", "r/technology"],
    },
    
    # LinkedIn Configuration
    "linkedin": {
        "enabled": True,
        "email": os.getenv("LINKEDIN_EMAIL", ""),
        "password": os.getenv("LINKEDIN_PASSWORD", ""),
        "post_interval": 86400,  # seconds between posts
        "max_posts_per_day": 1,
        "hashtags": ["#DreamOS", "#AI", "#Automation"],
    },
    
    # StockTwits Configuration
    "stocktwits": {
        "enabled": True,
        "username": os.getenv("STOCKTWITS_USERNAME", ""),
        "password": os.getenv("STOCKTWITS_PASSWORD", ""),
        "post_interval": 3600,  # seconds between posts
        "max_posts_per_day": 5,
        "hashtags": ["#DreamOS", "#AI", "#Automation"],
    },
    
    # Global Settings
    "global": {
        "headless": False,  # Run browsers in headless mode
        "proxy_rotation": False,  # Enable proxy rotation
        "retry_attempts": 3,  # Number of retry attempts for failed operations
        "timeout": 30,  # Default timeout for operations in seconds
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
}

def get_platform_config(platform: str) -> Dict[str, Any]:
    """Get configuration for a specific platform."""
    return social_config.get(platform, {})

def get_global_config() -> Dict[str, Any]:
    """Get global configuration settings."""
    return social_config.get("global", {}) 