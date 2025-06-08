"""Response Loop Daemon
-------------------
Base classes for response processing and daemon functionality.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages concurrent resource usage."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize the resource manager.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def acquire(self):
        """Acquire a resource slot."""
        await self.semaphore.acquire()
        
    def release(self):
        """Release a resource slot."""
        self.semaphore.release()

class ResponseErrorHandler:
    """Handles response processing errors."""
    
    def __init__(self, max_retries: int = 3):
        """Initialize the error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.retry_counts = {}
        
    async def handle_error(self, error: Exception, response_id: str) -> bool:
        """Handle a processing error.
        
        Args:
            error: The error that occurred
            response_id: ID of the response that failed
            
        Returns:
            True if should retry, False otherwise
        """
        if response_id not in self.retry_counts:
            self.retry_counts[response_id] = 0
            
        self.retry_counts[response_id] += 1
        
        if self.retry_counts[response_id] > self.max_retries:
            logger.error(f"Max retries exceeded for response {response_id}")
            return False
            
        # Exponential backoff
        delay = 2 ** (self.retry_counts[response_id] - 1)
        await asyncio.sleep(delay)
        return True

class ResponseProcessor(ABC):
    """Base class for response processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    @abstractmethod
    async def process(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            response: The response to process
            
        Returns:
            Dict containing the processed response
        """
        pass

class BaseResponseLoopDaemon:
    """Base class for response loop daemons."""
    
    def __init__(self, processor: ResponseProcessor, config: Optional[Dict[str, Any]] = None):
        """Initialize the daemon.
        
        Args:
            processor: The response processor to use
            config: Optional configuration dictionary
        """
        self.processor = processor
        self.config = config or {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the daemon."""
        if self.running:
            logger.warning("Daemon already running")
            return
            
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Daemon started")
        
    async def stop(self):
        """Stop the daemon."""
        if not self.running:
            logger.warning("Daemon not running")
            return
            
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Daemon stopped")
        
    async def _run(self):
        """Main daemon loop."""
        while self.running:
            try:
                # Get next response
                response = await self._get_next_response()
                if not response:
                    await asyncio.sleep(1)
                    continue
                    
                # Process response
                processed = await self.processor.process(response)
                
                # Handle processed response
                await self._handle_processed_response(processed)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                await asyncio.sleep(1)
                
    @abstractmethod
    async def _get_next_response(self) -> Optional[Dict[str, Any]]:
        """Get the next response to process.
        
        Returns:
            The next response or None if none available
        """
        pass
        
    @abstractmethod
    async def _handle_processed_response(self, response: Dict[str, Any]):
        """Handle a processed response.
        
        Args:
            response: The processed response
        """
        pass 
