"""
Configuration Management Module

Handles loading and managing recovery configuration settings.
Provides default values and configuration validation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ...config.unified_config import UnifiedConfigManager, ConfigSection
from ...utils.metrics import logger

class RecoveryConfigManager:
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
    
    VALIDATION_RULES = {
        "heartbeat_timeout": {"type": int, "min": 60, "max": 3600},
        "max_retries": {"type": int, "min": 1, "max": 10},
        "retry_cooldown": {"type": int, "min": 30, "max": 300},
        "restart_cooldown": {"type": int, "min": 60, "max": 600},
        "window_check_interval": {"type": int, "min": 10, "max": 300},
        "recovery_queue_timeout": {"type": int, "min": 60, "max": 3600},
        "max_concurrent_recoveries": {"type": int, "min": 1, "max": 10},
        "log_level": {"type": str, "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
        "enable_auto_recovery": {"type": bool},
        "enable_heartbeat_monitoring": {"type": bool}
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the recovery configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or "config/recovery_config.json"
        self._config_manager = UnifiedConfigManager(Path(self.config_path).parent)
        self._section = self._config_manager.get_section("recovery")
        
        # Initialize with defaults
        for key, value in self.DEFAULT_CONFIG.items():
            self._section.set(
                key,
                value,
                description=f"Recovery setting: {key}",
                validation_rules=self.VALIDATION_RULES.get(key)
            )
    
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            True if configuration loaded successfully
        """
        return self._config_manager.load_config(
            Path(self.config_path).stem,
            format=Path(self.config_path).suffix[1:]
        )
    
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            True if configuration saved successfully
        """
        return self._config_manager.save_config(
            Path(self.config_path).stem,
            format=Path(self.config_path).suffix[1:]
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return {
            key: self._section.get(key)
            for key in self.DEFAULT_CONFIG.keys()
        }
    
    def validate(self) -> bool:
        """Validate current configuration.
        
        Returns:
            True if configuration is valid
        """
        return self._section.validate() 