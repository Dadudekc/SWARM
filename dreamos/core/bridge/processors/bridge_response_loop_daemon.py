"""
Bridge response loop daemon for processing responses.
"""

import os
import time
import logging
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from dreamos.core.bridge.processors.response import ResponseProcessor
from dreamos.core.bridge.processors.message import MessageProcessor

logger = logging.getLogger(__name__)

class BridgeResponseLoopDaemon:
    """Daemon for processing bridge responses in a loop."""
    
    def __init__(
        self,
        response_processor: ResponseProcessor,
        message_processor: MessageProcessor,
        poll_interval: float = 1.0
    ):
        """Initialize the daemon.
        
        Args:
            response_processor: Processor for handling responses
            message_processor: Processor for handling messages
            poll_interval: Time between polling for new responses
        """
        self.response_processor = response_processor
        self.message_processor = message_processor
        self.poll_interval = poll_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start the response processing loop."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Bridge response loop daemon started")
    
    def stop(self) -> None:
        """Stop the response processing loop."""
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None
        logger.info("Bridge response loop daemon stopped")
    
    def _process_loop(self) -> None:
        """Main processing loop."""
        while self.running:
            try:
                # Process any pending responses
                responses = self.response_processor.get_pending_responses()
                for response in responses:
                    self.message_processor.process_response(response)
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in response loop: {e}")
                time.sleep(self.poll_interval)  # Still sleep on error 