"""
Configuration Management
---------------------
Manages configuration loading and validation for the test debug system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration loading and validation."""
    
    DEFAULT_CONFIG = {
        "paths": {
            "runtime": "runtime",
            "archive": "runtime/archive",
            "debug_logs": "runtime/debug_logs"
        },
        "test": {
            "timeout": 30,
            "retry_count": 3,
            "parallel": True
        },
        "fix": {
            "max_attempts": 3,
            "timeout": 60,
            "backoff_factor": 1.5
        }
    }
    
    def __init__(self, config_path: str):
        """Initialize the config manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    return self._validate_config(config)
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self.DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration structure.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validated configuration
        """
        # Ensure all required sections exist
        for section in self.DEFAULT_CONFIG:
            if section not in config:
                config[section] = self.DEFAULT_CONFIG[section]
            elif isinstance(self.DEFAULT_CONFIG[section], dict):
                # Ensure all required subsections exist
                for key, value in self.DEFAULT_CONFIG[section].items():
                    if key not in config[section]:
                        config[section][key] = value
        
        return config
    
    def get_path(self, path_type: str) -> Path:
        """Get a configured path.
        
        Args:
            path_type: Type of path to get
            
        Returns:
            Configured path
        """
        path = self.config["paths"].get(path_type)
        if not path:
            raise ValueError(f"Unknown path type: {path_type}")
        return Path(path)
    
    def get_test_config(self) -> Dict[str, Any]:
        """Get test configuration.
        
        Returns:
            Test configuration
        """
        return self.config["test"]
    
    def get_fix_config(self) -> Dict[str, Any]:
        """Get fix configuration.
        
        Returns:
            Fix configuration
        """
        return self.config["fix"]
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration.
        
        Args:
            updates: Configuration updates
        """
        try:
            # Deep merge updates
            self._deep_merge(self.config, updates)
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating config: {e}")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge two dictionaries.
        
        Args:
            target: Target dictionary
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value 
