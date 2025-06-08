from typing import Dict
import json
import logging
from pathlib import Path
import os

class CommunityBase:
    """Base class for community management modules."""
    
    def __init__(self, module_name: str, config_dir: str = None, log_dir: str = None):
        """Initialize the base community module.
        
        Args:
            module_name: Name of the module
            config_dir: Directory for configuration files
            log_dir: Directory for log files
        """
        self.module_name = module_name
        self.config_dir = config_dir or f"social/community/config/{module_name.lower()}_config.json"
        self.log_dir = log_dir or f"social/community/logs/{module_name.lower()}"
        self.config = self._load_config()
        self.metrics = {}
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup logging (sets self.logger)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the module."""
        log_file = os.path.join(self.log_dir, f"{self.module_name}.log")
        logging.basicConfig(
            filename=log_file,
            level=self.config.get("log_level", "INFO"),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.module_name)
    
    def _create_default_config(self) -> dict:
        """Create default configuration for the module.
        
        Returns:
            dict: Default configuration
        """
        return {
            "module_name": self.module_name,
            "enabled": True,
            "log_level": "INFO",
            "module": self.module_name,
            "metrics": {}
        }
    
    def _save_config(self, config: dict, config_path: str) -> bool:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary
            config_path: Path to save configuration
            
        Returns:
            bool: True if successful
            
        Raises:
            PermissionError: If unable to write to file or create directory
        """
        try:
            # Try to create directory first
            try:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
            except PermissionError:
                self.logger.error("Permission denied creating config directory")
                raise
                
            # Try to write file
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            except PermissionError:
                self.logger.error("Permission denied writing config file")
                raise
                
            return True
        except PermissionError:
            raise  # Re-raise PermissionError
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            return False
    
    def _load_config(self, config_path: str = None) -> dict:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            dict: Configuration dictionary
        """
        if config_path is None:
            config_path = os.path.join(self.config_dir, f"{self.module_name}.json")
            
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            
        return self._create_default_config()
    
    def _update_metrics(self, new_metrics: dict) -> None:
        """Update module metrics.
        
        Args:
            new_metrics: New metrics to update
        """
        if not isinstance(new_metrics, dict):
            raise ValueError("new_metrics must be a dictionary")
        self.metrics.update(new_metrics)
        self.logger.debug(f"Updated metrics: {new_metrics}") 
