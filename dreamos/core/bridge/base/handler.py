"""
Base Handler Interface
-------------------
Defines the interface that all bridge handlers must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from watchdog.events import FileSystemEventHandler

class BaseHandler(FileSystemEventHandler, ABC):
    """Base class for all bridge handlers."""
    
    def __init__(
        self,
        watch_dir: Path,
        file_pattern: str = "*.json",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the handler.
        
        Args:
            watch_dir: Directory to watch
            file_pattern: File pattern to match
            config: Optional configuration dictionary
        """
        super().__init__()
        self.watch_dir = watch_dir
        self.file_pattern = file_pattern
        self.config = config or {}
        self.processed_items: set[str] = set()
        
    @abstractmethod
    async def process_file(self, file_path: Path) -> None:
        """Process a file.
        
        Args:
            file_path: Path to file
        """
        pass
        
    @abstractmethod
    async def handle_error(self, error: Exception, file_path: Path) -> None:
        """Handle an error.
        
        Args:
            error: Error that occurred
            file_path: Path to file that caused error
        """
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
        
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith(self.file_pattern):
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.processed_items:
            return
            
        # Schedule file processing
        import asyncio
        asyncio.create_task(self.process_file(file_path))
        
    def on_modified(self, event):
        """Handle file modification event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith(self.file_pattern):
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.processed_items:
            return
            
        # Schedule file processing
        import asyncio
        asyncio.create_task(self.process_file(file_path)) 