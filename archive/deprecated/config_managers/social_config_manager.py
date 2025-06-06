import warnings
warnings.warn(
    "Deprecated: use dreamos.core.config.config_manager.ConfigManager instead.",
    DeprecationWarning,
)

"""
Configuration Manager Module
--------------------------
Handles loading and validation of configuration files.
"""

# Original implementation preserved for reference
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.dream_os'
        self.config_file = self.config_dir / 'config.json'
        self.default_config = {
            'log_level': 'INFO',
            'log_dir': str(self.config_dir / 'logs'),
            'max_log_size': 10 * 1024 * 1024,  # 10MB
            'max_log_files': 5,
            'output_format': 'json'
        }
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists with proper permissions."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Set directory permissions to user-only on Unix systems
            if os.name != 'nt':  # Not Windows
                os.chmod(self.config_dir, 0o700)
        except Exception as e:
            logging.error(f"Failed to create config directory: {e}")
            raise

    def _load_config(self) -> None:
        """Load configuration from file or create default if not exists."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self._validate_config()
            else:
                self.config = self.default_config.copy()
                self._save_config()
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            self.config = self.default_config.copy()

    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Ensure all required keys exist
        for key, default_value in self.default_config.items():
            if key not in self.config:
                self.config[key] = default_value

        # Validate log level
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.config['log_level'] not in valid_levels:
            self.config['log_level'] = 'INFO'

        # Validate log directory
        log_dir = Path(self.config['log_dir'])
        if not log_dir.is_absolute():
            self.config['log_dir'] = str(self.config_dir / log_dir)
        
        # Ensure log directory exists
        log_dir = Path(self.config['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)

        # Validate numeric values
        self.config['max_log_size'] = max(1024 * 1024, int(self.config['max_log_size']))  # Min 1MB
        self.config['max_log_files'] = max(1, min(100, int(self.config['max_log_files'])))  # Between 1-100

        # Validate output format
        valid_formats = {'json', 'text', 'yaml'}
        if self.config['output_format'] not in valid_formats:
            self.config['output_format'] = 'json'

    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            # Set file permissions to user-only on Unix systems
            if os.name != 'nt':  # Not Windows
                os.chmod(self.config_file, 0o600)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save to file."""
        self.config[key] = value
        self._validate_config()
        self._save_config()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.default_config.copy()
        self._save_config() 