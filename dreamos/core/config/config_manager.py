"""
Configuration Manager Module

Manages configuration for the Dream.OS system.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration for the Dream.OS system."""
    
    def __init__(self, config_dir: str):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            
        Returns:
            Configuration dictionary
        """
        # Try YAML first
        yaml_path = self.config_dir / f"{config_name}.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                return yaml.safe_load(f)
                
        # Try JSON next
        json_path = self.config_dir / f"{config_name}.json"
        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
                
        return {}
        
    def save_config(self, config_name: str, config: Dict[str, Any], format: str = "yaml") -> None:
        """Save a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            config: Configuration dictionary
            format: File format ("yaml" or "json")
        """
        if format == "yaml":
            path = self.config_dir / f"{config_name}.yaml"
            with open(path, "w") as f:
                yaml.dump(config, f)
        elif format == "json":
            path = self.config_dir / f"{config_name}.json"
            with open(path, "w") as f:
                json.dump(config, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def get_config_path(self, config_name: str, format: str = "yaml") -> Path:
        """Get the path to a configuration file.
        
        Args:
            config_name: Name of the configuration file (without extension)
            format: File format ("yaml" or "json")
            
        Returns:
            Path to the configuration file
        """
        if format == "yaml":
            return self.config_dir / f"{config_name}.yaml"
        elif format == "json":
            return self.config_dir / f"{config_name}.json"
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def config_exists(self, config_name: str, format: str = "yaml") -> bool:
        """Check if a configuration file exists.
        
        Args:
            config_name: Name of the configuration file (without extension)
            format: File format ("yaml" or "json")
            
        Returns:
            True if the configuration file exists, False otherwise
        """
        return self.get_config_path(config_name, format).exists() 
