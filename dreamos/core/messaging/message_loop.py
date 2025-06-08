"""
Message Loop Module
-----------------
Handles message processing and delivery.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from .common import Message
from .enums import MessageMode

logger = logging.getLogger(__name__)

class MessageLoop:
    """Asynchronous message loop for processing messages."""
    
    def __init__(self, queue: asyncio.Queue, handler: Callable[[Message], Awaitable[None]]):
        """Initialize message loop.
        
        Args:
            queue: Async queue for messages
            handler: Async function to handle messages
        """
        self.queue = queue
        self.handler = handler
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the message loop."""
        if self.running:
            logger.warning("Message loop already running")
            return
            
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Message loop started")
        
    async def stop(self):
        """Stop the message loop."""
        if not self.running:
            logger.warning("Message loop not running")
            return
            
        logger.info("Stopping message loop")
        self.running = False
        
        # Cancel task if running
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            
    async def _run(self):
        """Run the message loop."""
        try:
            while self.running:
                try:
                    # Get message from queue with timeout
                    try:
                        message = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        continue
                    
                    # Process message
                    await self.handler(message)
                    
                    # Mark task as done
                    self.queue.task_done()
                    
                except asyncio.CancelledError:
                    logger.info("Message loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except asyncio.CancelledError:
            logger.info("Message loop cancelled")
        except Exception as e:
            logger.error(f"Message loop error: {e}")
        finally:
            self.running = False
            logger.info("Message loop stopped")
            
    async def wait_for_stop(self, timeout: float = 1.0):
        """Wait for the message loop to stop.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        if not self._task:
            return
            
        try:
            await asyncio.wait_for(self._task, timeout=timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            # Ensure task is cancelled
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass 
