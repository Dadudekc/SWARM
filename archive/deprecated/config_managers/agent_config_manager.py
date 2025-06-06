"""Configuration utilities for Dream.OS."""

import warnings
warnings.warn(
    "dreamos.core.config.ConfigManager is deprecated. Use social.utils.config_manager.ConfigManager instead.",
    DeprecationWarning,
    stacklevel=2
)

import logging
from pathlib import Path
from typing import Dict, Any

from dreamos.core.utils.file_ops import (
    read_yaml, write_yaml,
    ensure_dir, safe_rmdir,
    FileOpsError, FileOpsPermissionError
)

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration loading and validation."""
    
    @staticmethod
    def load_agent_config(config_path: str) -> Dict[str, Any]:
        """Load agent configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration
            
        Raises:
            FileOpsError: If config file doesn't exist or is invalid
        """
        try:
            config = read_yaml(config_path)
            
            # Validate required fields
            required_fields = ["log_dir", "channel_assignments", "global_ui"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
                    
            return config
        except FileOpsError as e:
            raise FileOpsError(f"Failed to load config: {e}")
    
    @staticmethod
    def setup_test_environment() -> None:
        """Set up test environment.
        
        Raises:
            FileOpsPermissionError: If unable to create directories
        """
        try:
            # Create test directories
            test_dirs = [
                "tests/test_config",
                "tests/logs",
                "tests/data"
            ]
            
            for dir_path in test_dirs:
                ensure_dir(dir_path)
                
            # Create test config file
            config = {
                "log_dir": "tests/logs",
                "channel_assignments": {
                    "Agent-1": "general",
                    "Agent-2": "commands"
                },
                "global_ui": {
                    "input_box": {"x": 100, "y": 100},
                    "initial_spot": {"x": 200, "y": 200},
                    "copy_button": {"x": 300, "y": 300},
                    "response_region": {
                        "top_left": {"x": 400, "y": 400},
                        "bottom_right": {"x": 600, "y": 600}
                    }
                }
            }
            
            config_path = Path("tests/test_config/agent_config.yaml")
            write_yaml(str(config_path), config)
                
        except FileOpsPermissionError as e:
            raise FileOpsPermissionError(f"Failed to set up test environment: {e}")
    
    @staticmethod
    def cleanup_test_environment() -> None:
        """Clean up test environment.
        
        Raises:
            FileOpsPermissionError: If unable to remove directories
        """
        try:
            from tests.conftest import TEST_ROOT, TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR
            
            # Clean up test directories
            for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR]:
                if directory.exists():
                    safe_rmdir(str(directory), recursive=True)
                    
        except FileOpsPermissionError as e:
            raise FileOpsPermissionError(f"Failed to clean up test environment: {e}")
    
    @staticmethod
    def get_test_config() -> Dict[str, Any]:
        """Get test configuration.
        
        Returns:
            Dictionary containing test configuration
        """
        from tests.conftest import TEST_CONFIG_DIR
        config_path = TEST_CONFIG_DIR / "agent_config.yaml"
        return ConfigManager.load_agent_config(str(config_path)) 