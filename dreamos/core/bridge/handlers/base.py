"""
Base Bridge Handler
----------------
Core functionality for bridge handlers.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from watchdog.events import FileSystemEventHandler

from ...utils.core_utils import (
    load_json,
    save_json,
    atomic_write,
    safe_read,
    safe_write
)

# Configure logging
logger = logging.getLogger(__name__)

class BaseBridgeHandler(FileSystemEventHandler):
    """Base class for bridge handlers."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        watch_dir: Optional[Path] = None,
        file_pattern: str = "*.json"
    ):
        """Initialize the base handler.
        
        Args:
            config: Optional configuration dictionary
            watch_dir: Directory to watch for changes
            file_pattern: File pattern to watch
        """
        self.config = config or {}
        self.watch_dir = watch_dir or Path(self.config.get("paths", {}).get("bridge_outbox", "data/bridge_outbox"))
        self.file_pattern = file_pattern
        self.processed_items: Set[str] = set()
        
        # Ensure watch directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)
    
    async def _load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON data from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data or None if error
        """
        try:
            return await load_json(file_path)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return None
    
    async def _save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON data to file.
        
        Args:
            file_path: Path to save JSON file
            data: Data to save
            
        Returns:
            True if save successful
        """
        try:
            await save_json(file_path, data)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False
    
    async def _process_items(self):
        """Process items in the handler."""
        raise NotImplementedError
    
    async def _process_file(self, file_path: Path):
        """Process a file.
        
        Args:
            file_path: Path to file
        """
        raise NotImplementedError
    
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith(self.file_pattern):
            return
        
        asyncio.create_task(
            self._process_file(Path(event.src_path))
        )
    
    def on_modified(self, event):
        """Handle file modification event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith(self.file_pattern):
            return
        
        asyncio.create_task(
            self._process_file(Path(event.src_path))
        )
    
    async def start(self):
        """Start the handler."""
        await self._process_items()
    
    async def stop(self):
        """Stop the handler."""
        pass 