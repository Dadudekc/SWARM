"""
Configuration Management
---------------------
Manages configuration loading and validation for the test debug system.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ....config.unified_config import UnifiedConfigManager, ConfigSection
from ....utils.metrics import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDebugConfigManager:
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
    
    VALIDATION_RULES = {
        "paths": {
            "runtime": {"type": str},
            "archive": {"type": str},
            "debug_logs": {"type": str}
        },
        "test": {
            "timeout": {"type": int, "min": 1, "max": 3600},
            "retry_count": {"type": int, "min": 1, "max": 10},
            "parallel": {"type": bool}
        },
        "fix": {
            "max_attempts": {"type": int, "min": 1, "max": 10},
            "timeout": {"type": int, "min": 1, "max": 3600},
            "backoff_factor": {"type": float, "min": 1.0, "max": 5.0}
        }
    }
    
    def __init__(self, config_path: str):
        """Initialize the config manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config_manager = UnifiedConfigManager(self.config_path.parent)
        self._sections = {}
        
        # Initialize sections with defaults
        for section_name, section_data in self.DEFAULT_CONFIG.items():
            section = self._config_manager.get_section(section_name)
            for key, value in section_data.items():
                section.set(
                    key,
                    value,
                    description=f"Test debug setting: {key}",
                    validation_rules=self.VALIDATION_RULES.get(section_name, {}).get(key)
                )
            self._sections[section_name] = section
            
        # Load configuration
        self._config_manager.load_config(self.config_path.stem)
    
    def get_path(self, path_type: str) -> Path:
        """Get a configured path.
        
        Args:
            path_type: Type of path to get
            
        Returns:
            Configured path
        """
        path = self._sections["paths"].get(path_type)
        if not path:
            raise ValueError(f"Unknown path type: {path_type}")
        return Path(path)
    
    def get_test_config(self) -> Dict[str, Any]:
        """Get test configuration.
        
        Returns:
            Test configuration
        """
        return {
            key: self._sections["test"].get(key)
            for key in self.DEFAULT_CONFIG["test"].keys()
        }
    
    def get_fix_config(self) -> Dict[str, Any]:
        """Get fix configuration.
        
        Returns:
            Fix configuration
        """
        return {
            key: self._sections["fix"].get(key)
            for key in self.DEFAULT_CONFIG["fix"].keys()
        }
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration.
        
        Args:
            updates: Configuration updates
        """
        try:
            # Update sections
            for section_name, section_updates in updates.items():
                if section_name in self._sections:
                    section = self._sections[section_name]
                    for key, value in section_updates.items():
                        section.set(key, value)
            
            # Save configuration
            self._config_manager.save_config(self.config_path.stem)
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
