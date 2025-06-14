"""
Unified configuration management system for Dream.OS.

This module provides a centralized configuration management system that handles
all configuration files across the project, including agent configs, bridge configs,
and system settings.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class ConfigType(Enum):
    """Types of configuration files."""
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"

@dataclass
class ConfigSection:
    """Represents a section of configuration."""
    name: str
    data: Dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

class ConfigManager:
    """Manages all configuration across the project."""
    
    def __init__(self, config_root: str = None):
        """Initialize the configuration manager.
        
        Args:
            config_root: Root directory for configuration files. If None, uses default.
        """
        self.config_root = config_root or os.path.join(os.path.dirname(__file__), "..", "..", "config")
        self.sections: Dict[str, ConfigSection] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files from the config directory."""
        # Load agent configurations
        self._load_config_section("agent", "agent_config.yaml", ConfigType.YAML)
        self._load_config_section("agent_roles", "agent_roles/default.json", ConfigType.JSON)
        self._load_config_section("agent_ownership", "agent_ownership.json", ConfigType.JSON)
        self._load_config_section("agent_regions", "agent_regions.json", ConfigType.JSON)
        self._load_config_section("agents", "agents.json", ConfigType.JSON)
        
        # Load bridge configurations
        self._load_config_section("bridge", "bridge_config.json", ConfigType.JSON)
        self._load_config_section("chatgpt_bridge", "chatgpt_bridge.yaml", ConfigType.YAML)
        self._load_config_section("cursor_bridge", "cursor_bridge_config.json", ConfigType.JSON)
        
        # Load system configurations
        self._load_config_section("system", "system_config.yaml", ConfigType.YAML)
        self._load_config_section("autonomy", "autonomy_config.json", ConfigType.JSON)
        self._load_config_section("content_loop", "content_loop_behavior.yaml", ConfigType.YAML)
        self._load_config_section("response_loop", "response_loop_config.json", ConfigType.JSON)
        
        # Load social configurations
        self._load_config_section("social", "social.json", ConfigType.JSON)
        self._load_config_section("discord", "discord_bot.json", ConfigType.JSON)
        self._load_config_section("reddit", "reddit.json", ConfigType.JSON)
        
        # Load validation configurations
        self._load_config_section("codex_patch", "codex_patch_config.json", ConfigType.JSON)
        self._load_config_section("codex_validator", "codex_validator_config.json", ConfigType.JSON)
        self._load_config_section("patch_apply", "patch_apply_config.json", ConfigType.JSON)
    
    def _load_config_section(self, section_name: str, file_path: str, config_type: ConfigType):
        """Load a configuration section from a file.
        
        Args:
            section_name: Name of the configuration section.
            file_path: Path to the configuration file.
            config_type: Type of configuration file.
        """
        full_path = os.path.join(self.config_root, file_path)
        if not os.path.exists(full_path):
            print(f"Warning: Configuration file not found: {full_path}")
            return
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if config_type == ConfigType.YAML:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self.sections[section_name] = ConfigSection(
                name=section_name,
                data=data
            )
        except Exception as e:
            print(f"Error loading configuration {section_name}: {str(e)}")
    
    def get_config(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            section: Configuration section name.
            key: Configuration key. If None, returns entire section.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default if not found.
        """
        if section not in self.sections:
            return default
        
        if key is None:
            return self.sections[section].data
        
        return self.sections[section].data.get(key, default)
    
    def set_config(self, section: str, key: str, value: Any) -> bool:
        """Set a configuration value.
        
        Args:
            section: Configuration section name.
            key: Configuration key.
            value: Value to set.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if section not in self.sections:
            return False
        
        self.sections[section].data[key] = value
        return self._save_config(section)
    
    def _save_config(self, section: str) -> bool:
        """Save a configuration section to its file.
        
        Args:
            section: Configuration section name.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if section not in self.sections:
            return False
        
        config_section = self.sections[section]
        try:
            with open(config_section.file_path, 'w', encoding='utf-8') as f:
                if config_section.config_type == ConfigType.YAML:
                    yaml.dump(config_section.data, f, default_flow_style=False)
                else:
                    json.dump(config_section.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration {section}: {str(e)}")
            return False
    
    def reload_config(self, section: str = None) -> bool:
        """Reload configuration from files.
        
        Args:
            section: Section to reload. If None, reloads all sections.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if section:
            if section in self.sections:
                file_path = self.sections[section].file_path
                config_type = self.sections[section].config_type
                self._load_config_section(section, os.path.basename(file_path), config_type)
                return True
            return False
        else:
            self._load_all_configs()
            return True

    def get_section(self, name: str) -> ConfigSection:
        return self.sections.setdefault(name, ConfigSection(name, {}))

# Global configuration manager instance
config_manager = ConfigManager()

def get_config(section: str, key: str = None, default: Any = None) -> Any:
    """Get a configuration value from the global config manager.
    
    Args:
        section: Configuration section name.
        key: Configuration key. If None, returns entire section.
        default: Default value if key not found.
        
    Returns:
        Configuration value or default if not found.
    """
    return config_manager.get_config(section, key, default)

def set_config(section: str, key: str, value: Any) -> bool:
    """Set a configuration value in the global config manager.
    
    Args:
        section: Configuration section name.
        key: Configuration key.
        value: Value to set.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    return config_manager.set_config(section, key, value)

def reload_config(section: str = None) -> bool:
    """Reload configuration from files using the global config manager.
    
    Args:
        section: Section to reload. If None, reloads all sections.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    return config_manager.reload_config(section)

def get_section(name: str) -> ConfigSection:
    return config_manager.get_section(name)

def set_value(section: str, key: str, value: Any) -> None:
    config_manager.sections.setdefault(section, ConfigSection(name=section)).data[key] = value

def get_value(section: str, key: str, default: Any = None) -> Any:
    return config_manager.sections.get(section, ConfigSection(name=section)).data.get(key, default)

# ---------------------------------------------------------------------------
# Backwards-compatibility aliases for legacy import paths
# ---------------------------------------------------------------------------
class UnifiedConfigManager(ConfigManager):  # pragma: no cover – alias shim
    """Legacy alias for ConfigManager expected by older code/tests."""

    # Inherit everything without change
    pass

# Ensure symbol is part of public API if __all__ is defined
if '__all__' in globals():
    globals()['__all__'].append('UnifiedConfigManager')
else:
    __all__ = ['UnifiedConfigManager'] 