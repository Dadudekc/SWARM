"""
Base Bridge Handler
----------------
Base class for bridge handlers with unified file system event handling.
"""

import logging
from pathlib import Path
from typing import Optional, Set
from dreamos.core.autonomy.base.file_handler import BaseFileHandler

logger = logging.getLogger(__name__)

class BaseHandler(BaseFileHandler):
    """Base class for bridge handlers with unified file system event handling."""
    
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
        super().__init__(
            watch_dir=watch_dir,
            file_pattern=file_pattern,
            process_callback=process_callback,
            error_callback=error_callback,
            max_retries=max_retries,
            retry_delay=retry_delay,
            logger=logger
        )
        self.processed_items: Set[str] = set()
    
    async def process_file(self, file_path: Path) -> None:
        """Process a file.
        
        Args:
            file_path: Path to process
        """
        if file_path.name in self.processed_items:
            return
            
        try:
            # Get file manager for atomic operations
            manager = self.get_file_manager(file_path)
            
            # Process file
            await self.process_callback(file_path)
            
            # Mark as processed
            self.processed_items.add(file_path.name)
            
            # Log success
            self.logger.info(
                "file_processed",
                extra={
                    "path": str(file_path),
                    "pattern": self.file_pattern
                }
            )
            
        except Exception as e:
            if self.error_callback:
                await self.error_callback(e, file_path)
            self.logger.error(
                "file_processing_error",
                extra={
                    "path": str(file_path),
                    "error": str(e)
                }
            )
    
    async def cleanup(self):
        """Clean up resources."""
        await super().cleanup()
        self.processed_items.clear()

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
        super().__init__(watch_dir, file_pattern, self.process_file, self.handle_error, max_retries=3, retry_delay=1.0, logger=logger)
        self.config = config or {}
        
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