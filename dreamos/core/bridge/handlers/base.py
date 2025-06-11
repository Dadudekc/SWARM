"""
Base Handler Module
----------------
Provides base classes and shared functionality for bridge handlers.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Callable
from watchdog.events import FileSystemEventHandler
import asyncio

from ..chatgpt.bridge import ChatGPTBridge
from ..monitoring.metrics import BridgeMetrics
from ..monitoring.discord import DiscordHook, EventType

logger = logging.getLogger(__name__)

class BaseBridgeHandler(FileSystemEventHandler):
    """Base class for all bridge handlers."""
    
    def __init__(
        self,
        bridge: ChatGPTBridge,
        directory: Path,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the base handler.
        
        Args:
            bridge: ChatGPT bridge instance
            directory: Directory to monitor
            config: Optional configuration dictionary
        """
        self.bridge = bridge
        self.directory = Path(directory)
        self.config = config or {}
        self.metrics = BridgeMetrics()
        self.discord = DiscordHook()
        
        # Set up paths
        self.archive_dir = Path(self.config.get("paths", {}).get("archive", "data/archive"))
        self.failed_dir = Path(self.config.get("paths", {}).get("failed", "data/failed"))
        
        # Create directories
        for directory in [self.directory, self.archive_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Track processed items
        self.processed_items: Set[str] = set()
        
        # Initialize watchdog observer
        from watchdog.observers import Observer
        self.observer = Observer()
        self.observer.schedule(self, str(self.directory), recursive=False)
        
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith('.json'):
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.processed_items:
            return
            
        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Process file asynchronously
        loop.create_task(self._process_file(file_path))
        
    async def _process_file(self, file_path: Path):
        """Process a file.
        
        Args:
            file_path: Path to file
        """
        try:
            # Load message data
            message = await self._load_json(str(file_path))
            if not message:
                return
                
            # Process message
            await self._process_message(message)
            
            # Move to archive
            archive_path = self.archive_dir / file_path.name
            await self._move_to_archive(file_path, archive_path)
            
            # Mark as processed
            self.processed_items.add(file_path.name)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            await self._handle_error(file_path, str(e))
            
    async def _process_message(self, message: Dict[str, Any]):
        """Process a message.
        
        Args:
            message: Message to process
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _process_message()")
        
    async def _load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data or None if invalid
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return None
            
    async def _move_to_archive(self, source: Path, target: Path):
        """Move file to archive.
        
        Args:
            source: Source file path
            target: Target file path
        """
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        except Exception as e:
            logger.error(f"Error moving file to archive: {e}")
            await self._handle_error(source, str(e))
            
    async def _handle_error(self, file_path: Path, error: str):
        """Handle processing error.
        
        Args:
            file_path: Path to file that caused error
            error: Error message
        """
        try:
            # Move to failed directory
            failed_path = self.failed_dir / file_path.name
            await self._move_to_archive(file_path, failed_path)
            
            # Send Discord notification
            self.discord.send_event(
                EventType.ERROR,
                f"Failed to process file: {file_path.name}",
                {"error": error}
            )
            
            # Update metrics
            self.metrics.record_error(error)
            
        except Exception as e:
            logger.error(f"Error handling error: {e}")
            
    async def cleanup(self):
        """Clean up resources."""
        self.processed_items.clear()

    async def start(self) -> bool:
        """Start the handler.
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Start monitoring
            self.observer.start()
            return True
        
        except Exception as e:
            logger.error(f"Error starting handler: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the handler.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            # Stop monitoring
            self.observer.stop()
            self.observer.join()
            return True
        
        except Exception as e:
            logger.error(f"Error stopping handler: {e}")
            return False 