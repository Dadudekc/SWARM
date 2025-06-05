"""
Bridge Configuration Module
--------------------------
Provides configuration management for Dream.OS bridges.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("bridge_config")

class BridgeConfig:
    """Configuration for Dream.OS bridges."""
    
    def __init__(
        self,
        headless: bool = False,
        window_size: tuple = (1920, 1080),
        page_load_wait: int = 10,
        element_wait: int = 5,
        response_wait: int = 5,
        paste_delay: float = 0.5,
        health_check_interval: int = 30,
        user_data_dir: Optional[str] = None,
        cursor_window_title: str = "Cursor – agent"
    ):
        """Initialize bridge configuration.
        
        Args:
            headless: Run browser in headless mode
            window_size: Browser window size (width, height)
            page_load_wait: Page load timeout in seconds
            element_wait: Element wait timeout in seconds
            response_wait: Response wait time in seconds
            paste_delay: Delay between paste operations
            health_check_interval: Health check interval in seconds
            user_data_dir: Chrome user data directory
            cursor_window_title: Cursor window title
        """
        self.headless = headless
        self.window_size = window_size
        self.page_load_wait = page_load_wait
        self.element_wait = element_wait
        self.response_wait = response_wait
        self.paste_delay = paste_delay
        self.health_check_interval = health_check_interval
        self.user_data_dir = user_data_dir
        self.cursor_window_title = cursor_window_title
    
    @classmethod
    def load(cls, config_path: str) -> "BridgeConfig":
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            BridgeConfig instance
        """
        try:
            with open(config_path) as f:
                config = json.load(f)
            return cls(**config)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return cls()
    
    def save(self, config_path: str):
        """Save configuration to file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            config = {
                "headless": self.headless,
                "window_size": self.window_size,
                "page_load_wait": self.page_load_wait,
                "element_wait": self.element_wait,
                "response_wait": self.response_wait,
                "paste_delay": self.paste_delay,
                "health_check_interval": self.health_check_interval,
                "user_data_dir": self.user_data_dir,
                "cursor_window_title": self.cursor_window_title
            }
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved config to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            raise
    
    def validate(self):
        """Validate configuration values."""
        if not isinstance(self.window_size, tuple) or len(self.window_size) != 2:
            raise ValueError("window_size must be a tuple of (width, height)")
        
        if self.page_load_wait < 1:
            raise ValueError("page_load_wait must be at least 1 second")
        
        if self.element_wait < 1:
            raise ValueError("element_wait must be at least 1 second")
        
        if self.response_wait < 1:
            raise ValueError("response_wait must be at least 1 second")
        
        if self.paste_delay < 0:
            raise ValueError("paste_delay must be non-negative")
        
        if self.health_check_interval < 1:
            raise ValueError("health_check_interval must be at least 1 second") 