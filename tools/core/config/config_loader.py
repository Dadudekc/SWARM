"""
Configuration Loader
------------------
Loads and validates YAML configuration files for Dream.OS agents.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .schema import ConfigValidator

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and validates configuration files."""
    
    def __init__(self):
        """Initialize the config loader."""
        self.validator = ConfigValidator()
        self.root = Path(__file__).resolve().parent.parent.parent
        self.config_dir = self.root / "dreamos" / "config"
        self.agent_configs_dir = self.config_dir / "agent_configs"
    
    def load_config(self, agent_id: str) -> Dict[str, Any]:
        """Load configuration for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Merged configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Load default config
        default_config = self._load_yaml(self.config_dir / "default_config.yaml")
        if not default_config:
            default_config = self.validator.get_default_config()
        
        # Load agent-specific config
        agent_config = self._load_yaml(self.agent_configs_dir / f"{agent_id}.yaml")
        
        # Merge configs
        config = self._merge_configs(default_config, agent_config or {})
        
        # Format paths with agent_id
        config = self._format_paths(config, agent_id)
        
        # Validate final config
        is_valid, errors = self.validator.validate(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {errors}")
        
        logger.info(f"Loaded configuration for agent {agent_id}")
        logger.debug(f"Configuration: {config}")
        
        return config
    
    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Dictionary from YAML or None if file doesn't exist
        """
        try:
            if not path.exists():
                return None
            
            with path.open() as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error(f"Error loading YAML from {path}: {e}")
            return None
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configurations, with override taking precedence.
        
        Args:
            default: Default configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _format_paths(self, config: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Format paths with agent_id.
        
        Args:
            config: Configuration dictionary
            agent_id: Agent identifier
            
        Returns:
            Configuration with formatted paths
        """
        if 'paths' not in config:
            return config
        
        paths = config['paths']
        for key, path in paths.items():
            if isinstance(path, str):
                paths[key] = path.format(agent_id=agent_id)
        
        return config 
