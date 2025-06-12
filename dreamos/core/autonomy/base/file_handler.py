"""
Base File Handler
---------------
Base class for file system event handlers with unified event processing.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable, Awaitable, Set, Dict, Any
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from dreamos.core.utils.file_ops import FileManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseFileHandler(FileSystemEventHandler):
    """Base class for file system event handlers with unified event processing."""
    
    def __init__(
        self,
        watch_dir: Path,
        file_pattern: str,
        process_callback: Callable[[Path], Awaitable[None]],
        error_callback: Optional[Callable[[Exception, Path], Awaitable[None]]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the handler.
        
        Args:
            watch_dir: Directory to watch
            file_pattern: File pattern to match (e.g. "*.json")
            process_callback: Async callback to process matched files
            error_callback: Optional callback for error handling
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            logger: Optional logger instance
        """
        self.watch_dir = watch_dir
        self.file_pattern = file_pattern
        self.process_callback = process_callback
        self.error_callback = error_callback
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)
        self.processed_items: Set[str] = set()
        self.file_managers: Dict[str, FileManager] = {}
    
    def _should_process(self, event: FileSystemEvent) -> bool:
        """Check if event should be processed.
        
        Args:
            event: File system event
            
        Returns:
            bool: True if event should be processed
        """
        if event.is_directory:
            return False
            
        file_path = Path(event.src_path)
        if not file_path.match(self.file_pattern):
            return False
            
        if file_path.name in self.processed_items:
            return False
            
        return True
    
    async def _process_file(self, file_path: Path) -> bool:
        """Process a file with retries.
        
        Args:
            file_path: Path to process
            
        Returns:
            bool: True if processing succeeded
        """
        for attempt in range(self.max_retries):
            try:
                await self.process_callback(file_path)
                self.processed_items.add(file_path.name)
                return True
            except Exception as e:
                if self.error_callback:
                    await self.error_callback(e, file_path)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error(
                        "file_processing_error",
                        extra={
                            "path": str(file_path),
                            "error": str(e),
                            "attempts": self.max_retries
                        }
                    )
                    return False
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if not self._should_process(event):
            return
            
        file_path = Path(event.src_path)
        asyncio.create_task(self._process_file(file_path))
        
        self.logger.info(
            "file_created",
            extra={
                "path": str(file_path),
                "pattern": self.file_pattern
            }
        )
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification event.
        
        Args:
            event: File system event
        """
        if not self._should_process(event):
            return
            
        file_path = Path(event.src_path)
        asyncio.create_task(self._process_file(file_path))
        
        self.logger.info(
            "file_modified",
            extra={
                "path": str(file_path),
                "pattern": self.file_pattern
            }
        )
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion event.
        
        Args:
            event: File system event
        """
        if not self._should_process(event):
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.processed_items:
            self.processed_items.remove(file_path.name)
        
        self.logger.info(
            "file_deleted",
            extra={
                "path": str(file_path),
                "pattern": self.file_pattern
            }
        )
    
    def get_file_manager(self, file_path: Path) -> FileManager:
        """Get or create a file manager for the given path.
        
        Args:
            file_path: Path to manage
            
        Returns:
            FileManager: File manager instance
        """
        if str(file_path) not in self.file_managers:
            self.file_managers[str(file_path)] = FileManager(
                file_path,
                max_retries=self.max_retries
            )
        return self.file_managers[str(file_path)]
    
    async def cleanup(self):
        """Clean up resources."""
        for manager in self.file_managers.values():
            await manager.cleanup()
        self.file_managers.clear()
        self.processed_items.clear() 
