"""
Unified Handler
-------------
Base class for all handlers in the system, providing common functionality
and standardized interfaces.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Callable, Awaitable

from .handler_utils import (
    safe_watch_file,
    structured_log,
    standard_result_wrapper,
    safe_json_operation
)

logger = logging.getLogger(__name__)

class UnifiedHandler(ABC):
    """Base class for all handlers in the system."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the handler.
        
        Args:
            name: Handler name/identifier
            config: Optional configuration dictionary
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.name = name
        self.config = config or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._active_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
    @abstractmethod
    async def handle(self, data: Any) -> Dict[str, Any]:
        """Handle incoming data.
        
        Args:
            data: Data to handle
            
        Returns:
            Dict containing handling result
        """
        pass
        
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate incoming data.
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if data is valid
        """
        pass
        
    async def start(self) -> None:
        """Start the handler."""
        logger.info(f"Starting handler: {self.name}")
        self._shutdown_event.clear()
        
    async def stop(self) -> None:
        """Stop the handler."""
        logger.info(f"Stopping handler: {self.name}")
        self._shutdown_event.set()
        
        # Cancel all active tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            
        self._active_tasks.clear()
        
    async def watch_file(
        self,
        file_path: Union[str, Path],
        process_callback: Callable[[Path], Awaitable[None]],
        error_callback: Optional[Callable[[Exception, Path], Awaitable[None]]] = None
    ) -> None:
        """Watch a file for changes.
        
        Args:
            file_path: Path to watch
            process_callback: Async callback to process the file
            error_callback: Optional callback for error handling
        """
        path = Path(file_path)
        
        async def watch_loop():
            while not self._shutdown_event.is_set():
                success = await safe_watch_file(
                    path,
                    process_callback,
                    error_callback,
                    self.max_retries,
                    self.retry_delay
                )
                if not success:
                    logger.error(f"Failed to process {path}")
                await asyncio.sleep(self.retry_delay)
                
        task = asyncio.create_task(watch_loop())
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)
        
    async def process_json_file(
        self,
        file_path: Union[str, Path],
        operation: Callable[[Dict[str, Any]], Awaitable[None]],
        default_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Process a JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            operation: Async operation to perform on JSON data
            default_data: Default data if file doesn't exist
            
        Returns:
            bool: True if processing succeeded
        """
        return await safe_json_operation(file_path, operation, default_data)
        
    def log_operation(
        self,
        status: str,
        message: str,
        tags: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log an operation with structured format.
        
        Args:
            status: Status string (e.g. 'success', 'error')
            message: Log message
            tags: Optional list of tags
            details: Optional additional details
            
        Returns:
            Dict containing structured log data
        """
        return structured_log(
            self.name,
            status,
            message,
            tags,
            details
        )
        
    async def execute_with_retry(
        self,
        operation: Callable[..., Awaitable[Any]],
        *args: Any,
        success_message: str = "Operation completed successfully",
        error_message: str = "Operation failed",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute an operation with retry logic and standard result format.
        
        Args:
            operation: Async operation to execute
            *args: Positional arguments for operation
            success_message: Message for successful execution
            error_message: Message for failed execution
            **kwargs: Keyword arguments for operation
            
        Returns:
            Dict containing operation result and metadata
        """
        return await standard_result_wrapper(
            operation,
            *args,
            success_message=success_message,
            error_message=error_message,
            **kwargs
        ) 