"""
Configuration Management Module

Handles loading and managing recovery configuration settings.
Provides default values and configuration validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages recovery configuration settings."""
    
    DEFAULT_CONFIG = {
        "heartbeat_timeout": 300,  # 5 minutes
        "max_retries": 3,
        "retry_cooldown": 60,  # 1 minute
        "restart_cooldown": 300,  # 5 minutes
        "window_check_interval": 30,  # 30 seconds
        "recovery_queue_timeout": 300,  # 5 minutes
        "max_concurrent_recoveries": 3,
        "log_level": "INFO",
        "enable_auto_recovery": True,
        "enable_heartbeat_monitoring": True
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or "config/recovery_config.json"
        self.config: Dict = self.DEFAULT_CONFIG.copy()
        
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            bool: True if configuration loaded successfully
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                return False
                
            with open(config_file, "r") as f:
                loaded_config = json.load(f)
                
            # Update config with loaded values
            self.config.update(loaded_config)
            
            # Validate configuration
            self._validate_config()
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
            
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            bool: True if configuration saved successfully
        """
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=4)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def get_config(self) -> Dict:
        """Get current configuration.
        
        Returns:
            Dict: Current configuration dictionary
        """
        return self.config.copy()
        
    def update_config(self, updates: Dict) -> bool:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            bool: True if configuration updated successfully
        """
        try:
            # Update config
            self.config.update(updates)
            
            # Validate configuration
            self._validate_config()
            
            # Save to file
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
            
    def _validate_config(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate numeric values
        for key, value in self.config.items():
            if key.endswith("_timeout") or key.endswith("_cooldown") or key.endswith("_interval"):
                if not isinstance(value, (int, float)) or value <= 0:
                    raise ValueError(f"Invalid {key}: must be positive number")
                    
        # Validate max_retries
        if not isinstance(self.config["max_retries"], int) or self.config["max_retries"] < 0:
            raise ValueError("max_retries must be non-negative integer")
            
        # Validate max_concurrent_recoveries
        if not isinstance(self.config["max_concurrent_recoveries"], int) or self.config["max_concurrent_recoveries"] < 1:
            raise ValueError("max_concurrent_recoveries must be positive integer")
            
        # Validate boolean values
        for key in ["enable_auto_recovery", "enable_heartbeat_monitoring"]:
            if not isinstance(self.config[key], bool):
                raise ValueError(f"{key} must be boolean")
                
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.config["log_level"] not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}") 