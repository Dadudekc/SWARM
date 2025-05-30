"""
Unified Social Configuration Module

Manages configuration for social media operations, combining robust platform management
with flexible asset handling and path management.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class Platform(Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    LINKEDIN = "linkedin"
    STOCKTWITS = "stocktwits"

# Base directory structure
BASE_DIR = Path(__file__).resolve().parent.parent
COOKIES_DIR = BASE_DIR / "cookies"
MEDIA_DIR = BASE_DIR / "media"
DEBUG_DIR = BASE_DIR / "debug"
PROFILES_DIR = BASE_DIR / "profiles"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
for directory in [COOKIES_DIR, MEDIA_DIR, DEBUG_DIR, PROFILES_DIR, CONFIG_DIR]:
    directory.mkdir(exist_ok=True)

class PlatformConfig:
    """Platform-specific configuration and asset management."""
    
    def __init__(self, name: str):
        """Initialize platform configuration.
        
        Args:
            name: Platform name (e.g., 'twitter', 'reddit')
        """
        self.name = name.lower()
        self.platform = Platform(self.name)
        
        # Platform-specific directories
        self.cookies_file = COOKIES_DIR / f"{self.name}.pkl"
        self.media_dir = MEDIA_DIR / self.name
        self.debug_dir = DEBUG_DIR / self.name
        self.profile_dir = PROFILES_DIR / self.name
        
        # Create platform-specific directories
        for directory in [self.media_dir, self.debug_dir, self.profile_dir]:
            directory.mkdir(exist_ok=True)
            
        # Platform configuration
        self.config = {}
        self.credentials = {}
        self.media_config = {}
        self.retry_config = {}
        self.logging_config = {}
        
    def __repr__(self) -> str:
        return f"<PlatformConfig name={self.name}>"
        
    def load_config(self) -> bool:
        """Load platform configuration from file.
        
        Returns:
            bool: True if config loaded successfully
        """
        config_file = CONFIG_DIR / f"{self.name}.json"
        if not config_file.exists():
            return False
            
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                self.config = data.get('config', {})
                self.credentials = data.get('credentials', {})
                self.media_config = data.get('media', {})
                self.retry_config = data.get('retry', {})
                self.logging_config = data.get('logging', {})
            return True
        except Exception:
            return False
            
    def save_config(self) -> bool:
        """Save platform configuration to file.
        
        Returns:
            bool: True if config saved successfully
        """
        config_file = CONFIG_DIR / f"{self.name}.json"
        try:
            data = {
                'config': self.config,
                'credentials': self.credentials,
                'media': self.media_config,
                'retry': self.retry_config,
                'logging': self.logging_config
            }
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

class SocialConfig:
    """Global social media configuration manager."""
    
    def __init__(self, logger: Optional[Any] = None):
        """Initialize social configuration.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger
        self.platforms = {p.name.lower(): PlatformConfig(p.name.lower()) 
                         for p in Platform}
        self.memory_updates = {
            "config_loads": 0,
            "config_errors": [],
            "last_action": None,
            "last_error": None
        }
        
    def get_platform(self, platform: str) -> PlatformConfig:
        """Get platform configuration.
        
        Args:
            platform: Platform name
            
        Returns:
            PlatformConfig instance
            
        Raises:
            ValueError: If platform is not supported
        """
        key = platform.lower()
        if key not in self.platforms:
            raise ValueError(f"Unknown platform: {platform}")
        return self.platforms[key]
        
    def _update_memory(self, action: str, success: bool, error: Optional[str] = None) -> None:
        """Update memory with action results.
        
        Args:
            action: Action performed
            success: Whether action succeeded
            error: Optional error message
        """
        self.memory_updates["last_action"] = {
            "action": action,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            if action == "load_config":
                self.memory_updates["config_loads"] += 1
        else:
            self.memory_updates["last_error"] = {
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            self.memory_updates["config_errors"].append({
                "error": error,
                "action": action,
                "timestamp": datetime.now().isoformat()
            })
            
    def get_memory_updates(self) -> Dict[str, Any]:
        """Get memory updates for monitoring.
        
        Returns:
            Dictionary containing memory updates
        """
        return self.memory_updates

# Global instance
social_config = SocialConfig() 