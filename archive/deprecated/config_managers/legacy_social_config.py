import warnings
warnings.warn(
    "Deprecated: use dreamos.core.config.config_manager.ConfigManager instead.",
    DeprecationWarning,
)

"""
Legacy Social Configuration
-------------------------
This module is deprecated. Use dreamos.core.config.config_manager.ConfigManager instead.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class SocialConfig:
    def __init__(self, config_path: Optional[str] = None, logger: Optional[Any] = None):
        """Initialize SocialConfig.
        
        Args:
            config_path: Optional path to config file. Defaults to social/config/social_config.json
            logger: Optional logger instance for logging operations
        """
        self.config = {}
        self.logger = logger
        self.config_path = config_path or os.path.join('social', 'config', 'social_config.json')
        self.memory_updates = {
            "config_loads": 0,
            "config_errors": [],
            "last_action": None,
            "last_error": None
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
    
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            bool: True if config loaded successfully, False otherwise
        """
        try:
            if not Path(self.config_path).exists():
                self._update_memory("load_config", False, error="Config file not found")
                if self.logger:
                    self.logger.write_log(
                        platform="config",
                        status="error",
                        error="Config file not found",
                        tags=["config", "load"]
                    )
                return False
                
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                self._update_memory("load_config", True)
                if self.logger:
                    self.logger.write_log(
                        platform="config",
                        status="success",
                        tags=["config", "load"]
                    )
                return True
        except Exception as e:
            self._update_memory("load_config", False, error=str(e))
            if self.logger:
                self.logger.write_log(
                    platform="config",
                    status="error",
                    error=str(e),
                    tags=["config", "load"]
                )
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file.
        
        Returns:
            bool: True if config saved successfully, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
                self._update_memory("save_config", True)
                if self.logger:
                    self.logger.write_log(
                        platform="config",
                        status="success",
                        tags=["config", "save"]
                    )
                return True
        except Exception as e:
            self._update_memory("save_config", False, error=str(e))
            if self.logger:
                self.logger.write_log(
                    platform="config",
                    status="error",
                    error=str(e),
                    tags=["config", "save"]
                )
            return False
    
    def get(self, key, default=None):
        """Get a configuration value using dot notation."""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Set a configuration value using dot notation."""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def update(self, updates):
        """Update multiple configuration values."""
        self.config.update(updates)
    
    def get_platform_config(self, platform):
        """Get platform-specific configuration."""
        return self.config.get(platform, {})
    
    def get_memory_updates(self):
        """Get memory updates for monitoring."""
        return self.memory_updates
    
    def _update_memory(self, action, success, error=None):
        """Update memory with action results."""
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