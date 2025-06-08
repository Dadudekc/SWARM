"""Base response loop implementation for all daemons."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Protocol, Set, TypeVar, List

from ..state import StateManager
from ..utils import AsyncFileWatcher

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ResponseLoopConfig(Protocol):
    """Configuration protocol for response loops."""
    check_interval: float
    max_retries: int
    poll_timeout: float
    state_file: str
    response_dir: str

@dataclass
class ResponseMetadata:
    """Metadata for response processing."""
    timestamp: datetime
    source: str
    priority: int
    retry_count: int = 0
    error: Optional[str] = None

class BaseResponseLoop(Generic[T], ABC):
    """Base class for all response loop daemons.
    
    Provides common functionality for:
    - File polling and response processing
    - State management and transitions
    - Error handling and recovery
    - Resource cleanup
    """
    
    def __init__(self, config: ResponseLoopConfig):
        """Initialize the response loop.
        
        Args:
            config: Configuration for the response loop
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_manager = StateManager()
        
        # Runtime state
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.processed_items: Set[str] = set()
        self.failed_items: Set[str] = set()
        self.in_progress_items: Set[str] = set()
        
        # Queues
        self.item_queue: asyncio.Queue[str] = asyncio.Queue()
        self.result_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        
        # Metrics
        self.start_time = datetime.now()
        self.total_processed = 0
        self.total_failed = 0
        self.total_retries = 0
        
        # Components
        self.file_watcher = AsyncFileWatcher(
            watch_dir=config.response_dir,
            poll_interval=config.check_interval
        )
    
    async def start(self) -> None:
        """Start the response loop."""
        if self.is_running:
            logger.warning("Response loop already running")
            return
        
        logger.info("Starting response loop")
        self.is_running = True
        self.worker_task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """Stop the response loop."""
        if not self.is_running:
            logger.warning("Response loop not running")
            return
        
        logger.info("Stopping response loop")
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup
        self.processed_items.clear()
        self.failed_items.clear()
        self.in_progress_items.clear()
        self.total_processed = 0
        self.total_failed = 0
        self.total_retries = 0
        
        while not self.item_queue.empty():
            self.item_queue.get_nowait()
        
        while not self.result_queue.empty():
            self.result_queue.get_nowait()
    
    async def _run_loop(self) -> None:
        """Main loop for processing responses."""
        try:
            while self.is_running:
                # Check for new responses
                new_files = await self.file_watcher.check_for_changes()
                
                for file_path in new_files:
                    if file_path in self.processed_items or file_path in self.failed_items:
                        continue
                    
                    try:
                        # Load and validate response
                        response_data = await self._load_response(Path(file_path))
                        if not self._validate_response(response_data):
                            logger.warning(f"Invalid response in {file_path}")
                            self.failed_items.add(file_path)
                            self.total_failed += 1
                            continue
                        
                        # Queue for processing
                        await self.item_queue.put(file_path)
                        self.in_progress_items.add(file_path)
                        
                    except Exception as e:
                        logger.error(f"Error loading response {file_path}: {e}")
                        self.failed_items.add(file_path)
                        self.total_failed += 1
                
                # Process queued items
                while not self.item_queue.empty():
                    file_path = await self.item_queue.get()
                    
                    try:
                        # Load response data
                        response_data = await self._load_response(Path(file_path))
                        
                        # Process item
                        result = await self._handle_item(response_data)
                        
                        # Update state
                        self.processed_items.add(file_path)
                        self.in_progress_items.remove(file_path)
                        self.total_processed += 1
                        
                        # Queue result
                        await self.result_queue.put({
                            "file": file_path,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        self.failed_items.add(file_path)
                        self.in_progress_items.remove(file_path)
                        self.total_failed += 1
                
                # Save state
                await self._save_state()
                
                # Wait for next check
                await asyncio.sleep(self.config.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Response loop cancelled")
        except Exception as e:
            logger.error(f"Error in response loop: {e}")
            self.is_running = False
        finally:
            await self._save_state()
    
    async def _save_state(self) -> None:
        """Save current state to file."""
        state = {
            "processed_items": list(self.processed_items),
            "failed_items": list(self.failed_items),
            "in_progress_items": list(self.in_progress_items),
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_retries": self.total_retries,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(self.config.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    @abstractmethod
    async def _handle_item(self, item: T) -> Any:
        """Handle a response item.
        
        Args:
            item: The response item to handle
            
        Returns:
            Result of handling the item
        """
        pass
    
    @abstractmethod
    async def _load_response(self, response_file: Path) -> T:
        """Load a response from file.
        
        Args:
            response_file: Path to the response file
            
        Returns:
            Loaded response data
        """
        pass
    
    @abstractmethod
    def _validate_response(self, response_data: T) -> bool:
        """Validate response data.
        
        Args:
            response_data: Response data to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        pass

class ResponseLoop(BaseResponseLoop[T]):
    """Concrete implementation of response loop.
    
    This class provides a concrete implementation of the base response loop
    with default implementations for loading and validating responses.
    """
    
    async def _load_response(self, response_file: Path) -> T:
        """Load a response from file.
        
        Args:
            response_file: Path to the response file
            
        Returns:
            Loaded response data
        """
        try:
            with open(response_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading response from {response_file}: {e}")
            raise
    
    def _validate_response(self, response_data: T) -> bool:
        """Validate response data.
        
        Args:
            response_data: Response data to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        if not isinstance(response_data, dict):
            return False
            
        required_fields = ['type', 'data', 'metadata']
        return all(field in response_data for field in required_fields)
    
    async def _handle_item(self, item: T) -> Any:
        """Handle a response item.
        
        Args:
            item: The response item to handle
            
        Returns:
            Result of handling the item
        """
        try:
            response_type = item['type']
            response_data = item['data']
            metadata = item['metadata']
            
            # Process based on type
            if response_type == 'message':
                return await self._handle_message(response_data, metadata)
            elif response_type == 'command':
                return await self._handle_command(response_data, metadata)
            elif response_type == 'event':
                return await self._handle_event(response_data, metadata)
            else:
                logger.warning(f"Unknown response type: {response_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error handling item: {e}")
            raise
    
    async def _handle_message(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Handle a message response.
        
        Args:
            data: Message data
            metadata: Response metadata
            
        Returns:
            Result of handling the message
        """
        raise NotImplementedError("Message handling not implemented")
    
    async def _handle_command(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Handle a command response.
        
        Args:
            data: Command data
            metadata: Response metadata
            
        Returns:
            Result of handling the command
        """
        raise NotImplementedError("Command handling not implemented")
    
    async def _handle_event(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Handle an event response.
        
        Args:
            data: Event data
            metadata: Response metadata
            
        Returns:
            Result of handling the event
        """
        raise NotImplementedError("Event handling not implemented")

class ResponseLoop:
    """Response loop for agent communication."""
    
    def __init__(self, max_queue_size: int = 1000):
        """Initialize response loop.
        
        Args:
            max_queue_size: Maximum number of responses to queue
        """
        self.queue: List[Dict[str, Any]] = []
        self.max_queue_size = max_queue_size
        self._lock = asyncio.Lock()
        
    async def add_response(self, response: Dict[str, Any]) -> None:
        """Add a response to the queue.
        
        Args:
            response: Response dictionary
        """
        async with self._lock:
            if len(self.queue) >= self.max_queue_size:
                logger.warning("Response queue full, dropping oldest response")
                self.queue.pop(0)
            self.queue.append(response)
            
    async def next_response(self) -> Optional[Dict[str, Any]]:
        """Get next response from queue.
        
        Returns:
            Next response or None if queue empty
        """
        async with self._lock:
            return self.queue.pop(0) if self.queue else None
            
    async def peek_response(self) -> Optional[Dict[str, Any]]:
        """Peek at next response without removing it.
        
        Returns:
            Next response or None if queue empty
        """
        async with self._lock:
            return self.queue[0] if self.queue else None
            
    def clear(self) -> None:
        """Clear all responses."""
        self.queue.clear()
        
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Returns:
            bool: True if queue is empty
        """
        return len(self.queue) == 0
        
    @property
    def queue_size(self) -> int:
        """Get current queue size.
        
        Returns:
            int: Number of responses in queue
        """
        return len(self.queue) 
