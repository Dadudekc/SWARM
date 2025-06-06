"""
Security Configuration Module

Handles loading and validation of security-related configuration settings
for authentication, session management, and identity handling.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class SecurityConfig:
    """Manages security-related configuration settings."""
    
    DEFAULT_CONFIG = {
        'auth': {
            'token_expiry': 3600,  # 1 hour
            'refresh_token_expiry': 604800,  # 7 days
            'max_login_attempts': 5,
            'lockout_duration': 300,  # 5 minutes
        },
        'session': {
            'max_sessions_per_user': 5,
            'session_timeout': 1800,  # 30 minutes
            'cleanup_interval': 300,  # 5 minutes
        },
        'identity': {
            'min_password_length': 8,
            'require_special_chars': True,
            'password_history_size': 5,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize security configuration.
        
        Args:
            config_path: Optional path to custom config file. If not provided,
                        uses default location in user config directory.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = os.path.expanduser('~/.config/dreamos')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'security_config.json')
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                return self._validate_and_merge_config(config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading security config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
            
    def _validate_and_merge_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and merge provided config with defaults."""
        merged = self.DEFAULT_CONFIG.copy()
        
        # Merge provided config with defaults
        for section in merged:
            if section in config:
                merged[section].update(config[section])
                
        return merged
        
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Error saving security config: {e}")
            
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration."""
        return self.config['auth']
        
    def get_session_config(self) -> Dict[str, Any]:
        """Get session management configuration."""
        return self.config['session']
        
    def get_identity_config(self) -> Dict[str, Any]:
        """Get identity management configuration."""
        return self.config['identity']
        
    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """Update configuration section with new values.
        
        Args:
            section: Configuration section to update ('auth', 'session', or 'identity')
            updates: Dictionary of new configuration values
        """
        if section not in self.config:
            raise ValueError(f"Invalid config section: {section}")
            
        self.config[section].update(updates)
        self._save_config(self.config) 