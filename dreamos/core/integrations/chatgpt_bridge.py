"""
ChatGPT Bridge Service

Main service for integrating with ChatGPT through browser automation.
"""

import asyncio
import logging
import os
import time
from typing import Optional, Dict, Any, List

from ..automation.browser_control import BrowserControl
from ..config.config_manager import ConfigManager
from ..messaging.request_queue import RequestQueue
from ..monitoring.bridge_health import BridgeHealthMonitor
from ..utils.core_utils import with_retry

logger = logging.getLogger('chatgpt_bridge')

class ChatGPTBridge:
    """Main service for ChatGPT integration."""
    
    def __init__(self, config_path: str):
        """Initialize bridge service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bridge_config()
        
        # Initialize components
        self.browser = BrowserControl(
            user_data_dir=self.config.get('user_data_dir'),
            window_title=self.config.get('cursor_window_title'),
            page_load_wait=self.config.get('page_load_wait'),
            response_wait=self.config.get('response_wait'),
            paste_delay=self.config.get('paste_delay')
        )
        
        self.queue = RequestQueue(
            queue_file=os.path.join('runtime', 'bridge_inbox', 'requests.json')
        )
        
        self.health = BridgeHealthMonitor(
            status_file=os.path.join('runtime', 'bridge_inbox', 'health.json'),
            check_interval=self.config.get('health_check_interval')
        )
        
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the bridge service."""
        if self._running:
            return
            
        self._running = True
        self.browser.start()
        self._process_task = asyncio.create_task(self._process_requests())
        logger.info("Bridge service started")
    
    async def stop(self):
        """Stop the bridge service."""
        if not self._running:
            return
            
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
                
        self.browser.stop()
        logger.info("Bridge service stopped")
    
    async def _process_requests(self):
        """Process requests in the queue."""
        while self._running:
            try:
                # Get pending requests
                requests = self.queue.get_pending_requests()
                if not requests:
                    await asyncio.sleep(1)
                    continue
                
                # Process each request
                for request in requests:
                    if not self._running:
                        break
                        
                    success = await self._process_single_request(request)
                    
                    # Update health metrics
                    self.health.update_metrics(
                        success_rate=100 if success else 0,
                        processing_time=time.time() - request.timestamp
                    )
                
                # Cleanup old requests periodically
                self.queue.cleanup_old_requests()
                
            except Exception as e:
                logger.error(f"Error processing requests: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _process_single_request(self, request: Request) -> bool:
        """Process a single request.
        
        Args:
            request: Request to process
            
        Returns:
            Whether processing was successful
        """
        try:
            # Navigate to chat
            self.browser.navigate_to(self.config["chatgpt_url"])
            
            # Wait for chat to load
            self.browser.wait_for_stable_element(
                "textarea",
                by="tag name",
                stability_time=2.0
            )
            
            # Send message
            self.browser.send_keys("textarea", request.message)
            self.browser.click("button[type='submit']")
            
            # Wait for response
            response = self.browser.wait_for_stable_element(
                "div[data-message-author-role='assistant']",
                stability_time=2.0
            )
            
            # Update request
            self.queue.update_request(
                request.id,
                "completed",
                response=response.text
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to process request: {e}")
            self.queue.update_request(
                request.id,
                "error",
                error=str(e),
                increment_retry=True
            )
            return False
    
    async def send_message(self, message: str) -> Optional[str]:
        """Send message to ChatGPT.
        
        Args:
            message: Message to send
            
        Returns:
            Response text if successful, None otherwise
        """
        # Add request to queue
        request = self.queue.add_request(message)
        
        # Wait for response with timeout
        start_time = time.time()
        timeout = self.config.get('response_timeout', 300)  # 5 minutes
        
        while time.time() - start_time < timeout:
            # Check request status
            if request.status == "completed":
                return request.response
            elif request.status == "error":
                return None
                
            await asyncio.sleep(1)
        
        # Timeout
        self.queue.update_request(
            request.id,
            "error",
            error="Request timed out"
        )
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Dictionary of queue statistics
        """
        return self.queue.get_queue_stats()
    
    def is_healthy(self) -> bool:
        """Check if bridge is healthy.
        
        Returns:
            Whether bridge is healthy
        """
        return self.health.check_health()

async def main() -> None:
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bridge = ChatGPTBridge('config/chatgpt_bridge.yaml')
    
    try:
        await bridge.start()
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await bridge.stop()
        
if __name__ == '__main__':
    asyncio.run(main()) 
