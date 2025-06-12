"""
Test Environment Utilities
------------------------
Provides utilities for setting up and managing the test environment.
"""

import os
import sys
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestEnvironment:
    """Manages test environment setup and cleanup."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize test environment.
        
        Args:
            base_dir: Base directory for test files. Defaults to temp directory.
        """
        self.base_dir = base_dir or Path(tempfile.mkdtemp(prefix="dreamos_test_"))
        self.test_dirs = {
            "data": self.base_dir / "data",
            "output": self.base_dir / "output",
            "runtime": self.base_dir / "runtime",
            "temp": self.base_dir / "temp",
            "config": self.base_dir / "config",
            "logs": self.base_dir / "logs",
            "voice_queue": self.base_dir / "voice_queue"
        }
        
    def setup(self) -> None:
        """Set up test environment."""
        try:
            # Create test directories
            for dir_path in self.test_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
                
            # Set environment variables
            os.environ["DREAMOS_TEST_MODE"] = "1"
            os.environ["DREAMOS_TEST_DATA_DIR"] = str(self.test_dirs["data"])
            os.environ["DREAMOS_TEST_CACHE_DIR"] = str(self.test_dirs["temp"])
            os.environ["DREAMOS_LOG_LEVEL"] = "DEBUG"
            
            logger.info(f"Test environment setup complete in {self.base_dir}")
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            raise
            
    def cleanup(self) -> None:
        """Clean up test environment."""
        try:
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
            logger.info("Test environment cleanup complete")
        except Exception as e:
            logger.error(f"Failed to cleanup test environment: {e}")
            raise
            
    @contextmanager
    def managed(self) -> Generator[None, None, None]:
        """Context manager for test environment."""
        try:
            self.setup()
            yield
        finally:
            self.cleanup()
            
    def get_test_dir(self, name: str) -> Path:
        """Get test directory by name.
        
        Args:
            name: Directory name (data, output, runtime, etc.)
            
        Returns:
            Path to test directory
        """
        if name not in self.test_dirs:
            raise ValueError(f"Unknown test directory: {name}")
        return self.test_dirs[name]
        
    def create_test_file(self, name: str, content: str = "") -> Path:
        """Create a test file.
        
        Args:
            name: File name
            content: File content
            
        Returns:
            Path to created file
        """
        file_path = self.test_dirs["temp"] / name
        file_path.write_text(content)
        return file_path
        
    def create_test_config(self, name: str, config: Dict[str, Any]) -> Path:
        """Create a test configuration file.
        
        Args:
            name: Config file name
            config: Configuration data
            
        Returns:
            Path to created config file
        """
        import json
        file_path = self.test_dirs["config"] / name
        file_path.write_text(json.dumps(config, indent=2))
        return file_path 