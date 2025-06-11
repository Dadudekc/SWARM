"""Configuration manager for tests."""

from typing import Dict, Any, Optional

class ConfigManager:
    """Manages test configuration."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
    
    def load(self, config: Dict[str, Any]) -> None:
        """Load configuration from dict."""
        self.config.update(config) 