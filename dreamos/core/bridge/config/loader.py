"""
Bridge Config Loader
-----------------
Handles loading and validation of bridge configurations.
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeMode(Enum):
    """Bridge operation modes."""
    TEST = "test"
    LIVE = "live"
    DEBUG = "debug"

class BridgeConfigLoader:
    """Loads and validates bridge configurations."""
    
    def __init__(
        self,
        base_config_path: Union[str, Path],
        mode: BridgeMode = BridgeMode.LIVE
    ):
        """Initialize the config loader.
        
        Args:
            base_config_path: Path to base config file
            mode: Bridge operation mode
        """
        self.base_config_path = Path(base_config_path)
        self.mode = mode
        self.config_dir = self.base_config_path.parent
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        
    def load_config(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration for an agent or base config.
        
        Args:
            agent_id: Optional agent ID to load config for
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        try:
            # Load base config
            with open(self.base_config_path) as f:
                base_config = json.load(f)
                
            # Load mode-specific overrides
            mode_config = self._load_mode_config()
            
            # Load agent-specific config if provided
            agent_config = {}
            if agent_id:
                agent_config = self._load_agent_config(agent_id)
                
            # Merge configs
            config = self._merge_configs(base_config, mode_config, agent_config)
            
            # Validate config
            self._validate_config(config)
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
            
    def _load_mode_config(self) -> Dict[str, Any]:
        """Load mode-specific configuration.
        
        Returns:
            Mode configuration dictionary
        """
        mode_config_path = self.config_dir / f"config.{self.mode.value}.json"
        
        if not mode_config_path.exists():
            return {}
            
        with open(mode_config_path) as f:
            return json.load(f)
            
    def _load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Load agent-specific configuration.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent configuration dictionary
        """
        # Check cache
        if agent_id in self.agent_configs:
            return self.agent_configs[agent_id]
            
        # Load from file
        agent_config_path = self.config_dir / "agents" / f"{agent_id}.json"
        
        if not agent_config_path.exists():
            return {}
            
        with open(agent_config_path) as f:
            config = json.load(f)
            
        # Cache config
        self.agent_configs[agent_id] = config
            
        return config
        
    def _merge_configs(
        self,
        base: Dict[str, Any],
        mode: Dict[str, Any],
        agent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge configuration dictionaries.
        
        Args:
            base: Base configuration
            mode: Mode-specific configuration
            agent: Agent-specific configuration
            
        Returns:
            Merged configuration
        """
        # Deep merge dictionaries
        def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            result = d1.copy()
            
            for key, value in d2.items():
                if (
                    key in result and
                    isinstance(result[key], dict) and
                    isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
                    
            return result
            
        # Merge in order: base -> mode -> agent
        config = deep_merge(base, mode)
        config = deep_merge(config, agent)
        
        return config
        
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If config is invalid
        """
        # Check required sections
        required = ["paths", "bridge", "handlers", "processors", "monitoring", "logging"]
        missing = [section for section in required if section not in config]
        
        if missing:
            raise ValueError(f"Missing required config sections: {missing}")
            
        # Validate paths
        paths = config["paths"]
        required_paths = ["base", "archive", "failed"]
        missing_paths = [path for path in required_paths if path not in paths]
        
        if missing_paths:
            raise ValueError(f"Missing required paths: {missing_paths}")
            
        # Validate bridge config
        bridge = config["bridge"]
        required_bridge = ["api_key", "model"]
        missing_bridge = [key for key in required_bridge if key not in bridge]
        
        if missing_bridge:
            raise ValueError(f"Missing required bridge config: {missing_bridge}")
            
    def save_agent_config(self, agent_id: str, config: Dict[str, Any]) -> None:
        """Save agent-specific configuration.
        
        Args:
            agent_id: Agent ID
            config: Configuration to save
        """
        # Create agents directory
        agents_dir = self.config_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save config
        agent_config_path = agents_dir / f"{agent_id}.json"
        
        with open(agent_config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        # Update cache
        self.agent_configs[agent_id] = config 