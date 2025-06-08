"""
Response Watcher
--------------
Monitors response outbox and forwards responses to WebSocket clients.
"""

import asyncio
import logging
import threading
from pathlib import Path
from typing import Dict, Set, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .response_queue import ResponseQueue, ResponseState

logger = logging.getLogger(__name__)

class ResponseEventHandler(FileSystemEventHandler):
    """Handler for response file events."""
    
    def __init__(self, response_queue: ResponseQueue, websocket_manager):
        """Initialize handler.
        
        Args:
            response_queue: Response queue instance
            websocket_manager: WebSocket manager instance
        """
        self.response_queue = response_queue
        self.websocket_manager = websocket_manager
        
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if not event.is_directory and event.src_path.endswith('.json'):
            try:
                # Extract agent_id and response_id from path
                path = Path(event.src_path)
                agent_id = path.parent.name
                response_id = path.stem
                
                # Get response
                response = self.response_queue.peek(agent_id)
                if not response or response["id"] != response_id:
                    return
                    
                # Forward to WebSocket clients
                asyncio.run_coroutine_threadsafe(
                    self.websocket_manager.broadcast_response(agent_id, response),
                    self.websocket_manager.loop
                )
                
                # Update state
                self.response_queue.update_response_state(
                    agent_id, response_id, ResponseState.SENT
                )
                
            except Exception as e:
                logger.error(f"Failed to handle response event: {e}")

class ResponseWatcher:
    """Watches response outbox and forwards responses."""
    
    def __init__(
        self,
        response_queue: ResponseQueue,
        websocket_manager,
        watch_interval: float = 1.0
    ):
        """Initialize watcher.
        
        Args:
            response_queue: Response queue instance
            websocket_manager: WebSocket manager instance
            watch_interval: Watch interval in seconds
        """
        self.response_queue = response_queue
        self.websocket_manager = websocket_manager
        self.watch_interval = watch_interval
        
        self.observer = Observer()
        self.handler = ResponseEventHandler(response_queue, websocket_manager)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start watching."""
        if self._running:
            return
            
        self._running = True
        
        # Start file system observer
        self.observer.schedule(
            self.handler,
            str(self.response_queue.outbox_dir),
            recursive=True
        )
        self.observer.start()
        
        # Start background thread
        self._thread = threading.Thread(target=self._watch_loop)
        self._thread.daemon = True
        self._thread.start()
        
        logger.info("Response watcher started")
        
    def stop(self):
        """Stop watching."""
        if not self._running:
            return
            
        self._running = False
        self.observer.stop()
        self.observer.join()
        
        if self._thread:
            self._thread.join()
            
        logger.info("Response watcher stopped")
        
    def _watch_loop(self):
        """Watch loop."""
        while self._running:
            try:
                # Check for pending responses
                for agent_dir in self.response_queue.outbox_dir.iterdir():
                    if not agent_dir.is_dir():
                        continue
                        
                    agent_id = agent_dir.name
                    pending = self.response_queue.get_pending_responses(agent_id)
                    
                    for response in pending:
                        # Forward to WebSocket clients
                        asyncio.run_coroutine_threadsafe(
                            self.websocket_manager.broadcast_response(
                                agent_id, response
                            ),
                            self.websocket_manager.loop
                        )
                        
                        # Update state
                        self.response_queue.update_response_state(
                            agent_id, response["id"], ResponseState.SENT
                        )
                        
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                
            # Sleep
            threading.Event().wait(self.watch_interval) 