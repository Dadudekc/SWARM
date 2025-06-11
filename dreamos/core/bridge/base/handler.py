"""
Base Handler Interface
-------------------
Defines the interface that all bridge handlers must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from watchdog.events import FileSystemEventHandler
import json
import logging
from datetime import datetime

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

class BridgeHandler(BaseHandler):
    """Bridge-specific handler implementation."""
    
    def __init__(
        self,
        watch_dir: Path,
        file_pattern: str = "*.json",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the bridge handler.
        
        Args:
            watch_dir: Directory to watch
            file_pattern: File pattern to match
            config: Optional configuration dictionary
        """
        super().__init__(watch_dir, file_pattern, config)
        self.logger = logging.getLogger(__name__)
        
    async def process_file(self, file_path: Path) -> None:
        """Process a bridge file.
        
        Args:
            file_path: Path to file
        """
        try:
            # Read and parse file
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Validate data
            if not self._validate_data(data):
                raise ValueError(f"Invalid data format in {file_path}")
                
            # Process data
            await self._process_data(data)
            
            # Mark as processed
            self.processed_items.add(file_path.name)
            
            # Clean up file
            file_path.unlink()
            
        except Exception as e:
            await self.handle_error(e, file_path)
            
    async def handle_error(self, error: Exception, file_path: Path) -> None:
        """Handle a bridge processing error.
        
        Args:
            error: Error that occurred
            file_path: Path to file that caused error
        """
        self.logger.error(
            f"Error processing {file_path}: {str(error)}",
            exc_info=True
        )
        
        # Move to error directory if configured
        error_dir = self.config.get('error_dir')
        if error_dir:
            error_path = Path(error_dir) / file_path.name
            file_path.rename(error_path)
            
    async def cleanup(self) -> None:
        """Clean up bridge handler resources."""
        self.processed_items.clear()
        
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate bridge data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['type', 'content']
        return all(field in data for field in required_fields)
        
    async def _process_data(self, data: Dict[str, Any]) -> None:
        """Process bridge data.
        
        Args:
            data: Data to process
        """
        # Add timestamp
        data['timestamp'] = datetime.utcnow().isoformat()
        
        # Add bridge config
        data['bridge_config'] = self.config
        
        # Log processing
        self.logger.info(f"Processing bridge data: {data}") 