"""
Base File Handler
---------------
Base class for file system event handlers.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable, Awaitable
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseFileHandler(FileSystemEventHandler):
    """Base class for file system event handlers."""
    
    def __init__(self, 
                 watch_dir: Path,
                 file_pattern: str,
                 process_callback: Callable[[Path], Awaitable[None]],
                 logger=None):
        """Initialize the handler.
        
        Args:
            watch_dir: Directory to watch
            file_pattern: File pattern to match (e.g. "*.json")
            process_callback: Async callback to process matched files
            logger: Optional logger instance
        """
        self.watch_dir = watch_dir
        self.file_pattern = file_pattern
        self.process_callback = process_callback
        self.logger = logger or logger
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if not file_path.match(self.file_pattern):
            return
            
        # Create task to process file
        asyncio.create_task(self.process_callback(file_path))
        
        # Log event
        if self.logger:
            self.logger.info(
                platform="file_handler",
                status="created",
                message=f"Detected new file: {file_path.name}",
                tags=["watch", "success"]
            )
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification event.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if not file_path.match(self.file_pattern):
            return
            
        # Create task to process file
        asyncio.create_task(self.process_callback(file_path))
        
        # Log event
        if self.logger:
            self.logger.info(
                platform="file_handler",
                status="modified",
                message=f"Detected modified file: {file_path.name}",
                tags=["watch", "success"]
            )
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion event.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if not file_path.match(self.file_pattern):
            return
            
        # Log event
        if self.logger:
            self.logger.info(
                platform="file_handler",
                status="deleted",
                message=f"Detected deleted file: {file_path.name}",
                tags=["watch", "success"]
            ) 
