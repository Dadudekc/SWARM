"""
Config Manager Module

Stubbed config manager for test unblocking.
"""

import warnings
warnings.warn(
    "dreamos.core.shared.config_manager.ConfigManager is deprecated. Use social.utils.config_manager.ConfigManager instead.",
    DeprecationWarning,
    stacklevel=2
)

from threading import Lock

class ConfigManager:
    """Stubbed config manager for test unblocking."""

    def __init__(self):
        self.config = {}
        self.lock = Lock()

    async def load_config(self, path: str) -> dict:
        return {"stub_key": "stub_value"}

    async def get_config(self, key: str, default=None):
        return self.config.get(key, default)

    def set_config(self, key: str, value) -> None:
        with self.lock:
            self.config[key] = value 