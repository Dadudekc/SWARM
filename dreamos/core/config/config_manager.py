"""
Unified Configuration Manager
---------------------------
Handles loading, validation, and management of all Dream.OS configuration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """Unified configuration manager for Dream.OS."""
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        default_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize configuration manager.
        
        Args:
            config_dir: Base configuration directory
            default_config: Default configuration values
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.dream_os'
        self.config_file = self.config_dir / 'config.json'
        
        # Default configuration
        self.default_config = default_config or {
            'log_level': 'INFO',
            'log_dir': str(self.config_dir / 'logs'),
            'max_log_size': 10 * 1024 * 1024,  # 10MB
            'max_log_files': 5,
            'output_format': 'json',
            'bridge': {
                'headless': False,
                'window_size': (1920, 1080),
                'page_load_wait': 10,
                'element_wait': 5,
                'response_wait': 5,
                'paste_delay': 0.5,
                'health_check_interval': 30,
                'user_data_dir': None,
                'cursor_window_title': "Cursor – agent"
            }
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
            logger.error(f"Failed to create config directory: {e}")
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
            logger.error(f"Failed to load config: {e}")
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
        
        # Validate bridge configuration
        bridge_config = self.config.get('bridge', {})
        if not isinstance(bridge_config.get('window_size'), (list, tuple)) or len(bridge_config.get('window_size', [])) != 2:
            bridge_config['window_size'] = self.default_config['bridge']['window_size']
        
        for key in ['page_load_wait', 'element_wait', 'response_wait', 'health_check_interval']:
            if bridge_config.get(key, 0) < 1:
                bridge_config[key] = self.default_config['bridge'][key]
        
        if bridge_config.get('paste_delay', -1) < 0:
            bridge_config['paste_delay'] = self.default_config['bridge']['paste_delay']
        
        self.config['bridge'] = bridge_config
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            # Set file permissions to user-only on Unix systems
            if os.name != 'nt':  # Not Windows
                os.chmod(self.config_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
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
    
    def get_bridge_config(self) -> Dict[str, Any]:
        """Get bridge-specific configuration."""
        return self.config.get('bridge', self.default_config['bridge'])
    
    def set_bridge_config(self, config: Dict[str, Any]) -> None:
        """Set bridge-specific configuration."""
        self.config['bridge'] = config
        self._validate_config()
        self._save_config() 