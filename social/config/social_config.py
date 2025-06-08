"""Social media configuration settings."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
from pathlib import Path
from enum import Enum

class Platform(Enum):
    """Supported social media platforms."""
    REDDIT = "reddit"
    TWITTER = "twitter"
    DISCORD = "discord"
    TELEGRAM = "telegram"

@dataclass
class PlatformConfig:
    """Configuration for a specific social media platform."""
    platform: Platform
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    rate_limit: Optional[int] = None
    enabled: bool = True

@dataclass
class SocialConfig:
    """Configuration for social media integration."""
    
    # Base paths
    base_dir: Path = Path(__file__).parent.parent
    config_dir: Path = base_dir / "config"
    data_dir: Path = base_dir / "data"
    
    # API settings
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    
    # Rate limiting
    rate_limit_enabled: bool = True
    default_rate_limit: int = 60  # requests per minute
    
    # Logging
    log_level: str = "INFO"
    log_dir: Path = base_dir / "logs"
    
    # Platform configs
    platforms: Dict[Platform, PlatformConfig] = None
    
    def __post_init__(self):
        """Ensure directories exist and initialize platform configs."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        if self.platforms is None:
            self.platforms = {
                platform: PlatformConfig(platform=platform)
                for platform in Platform
            }

# Global config instance
social_config = SocialConfig() 
