"""Configuration manager for tests."""

from typing import Dict, Any, Optional
from dreamos.core.config.unified_config import UnifiedConfigManager, ConfigSection

class TestConfigManager:
    """Manages test configuration."""
    
    def __init__(self):
        self._config_manager = UnifiedConfigManager("tests/config")
        self._section = self._config_manager.get_section("test")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._section.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._section.set(key, value)
    
    def load(self, config: Dict[str, Any]) -> None:
        """Load configuration from dict."""
        for key, value in config.items():
            self._section.set(key, value) 