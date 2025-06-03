"""
ChatGPT Bridge Service

Main service for integrating with ChatGPT through browser automation.
"""

import asyncio
import logging
import os
from typing import Optional

from ..automation.browser_control import BrowserControl
from ..config.bridge_config import BridgeConfig
from ..messaging.request_queue import RequestQueue
from ..monitoring.bridge_health import BridgeHealthMonitor
from ..utils.retry import with_retry

logger = logging.getLogger('chatgpt_bridge')

class ChatGPTBridge:
    """Main service for ChatGPT integration."""
    
    def __init__(self, config_path: str):
        """Initialize bridge service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = BridgeConfig.load(config_path)
        self.config.validate()
        
        # Initialize components
        self.browser = BrowserControl(
            user_data_dir=self.config.user_data_dir,
            window_title=self.config.cursor_window_title,
            page_load_wait=self.config.page_load_wait,
            response_wait=self.config.response_wait,
            paste_delay=self.config.paste_delay
        )
        
        self.queue = RequestQueue(
            queue_file=os.path.join('runtime', 'bridge_inbox', 'requests.json')
        )
        
        self.health = BridgeHealthMonitor(
            status_file=os.path.join('runtime', 'bridge_inbox', 'health.json'),
            check_interval=self.config.health_check_interval
        )
        
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start bridge service."""
        if self._running:
            return
            
        try:
            # Launch browser
            await self.launch_browser()
            
            # Start health monitoring
            await self.health.start()
            
            # Start request processing
            self._running = True
            self._process_task = asyncio.create_task(self._process_requests())
            
            logger.info("ChatGPT bridge service started")
            
        except Exception as e:
            logger.error(f"Failed to start bridge service: {e}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop bridge service."""
        if not self._running:
            return
            
        self._running = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None
            
        await self.health.stop()
        await self.browser.close_browser()
        
        logger.info("ChatGPT bridge service stopped")
        
    @with_retry(max_retries=3, backoff_factor=2.0)
    async def launch_browser(self) -> None:
        """Launch browser with retry logic."""
        await self.browser.launch_browser()
        self.health.update_health(
            is_healthy=True,
            session_active=True
        )
        
    async def send_message(self, message: str) -> str:
        """Send message to ChatGPT.
        
        Args:
            message: Message to send
            
        Returns:
            Response from ChatGPT
        """
        request = self.queue.add_request(message)
        
        try:
            response = await self.browser.send_message(message)
            self.queue.update_request(
                request.id,
                status='completed',
                response=response
            )
            self.health.update_health(
                is_healthy=True,
                message_count=self.health.health.message_count + 1
            )
            return response
            
        except Exception as e:
            self.queue.update_request(
                request.id,
                status='failed',
                error=str(e)
            )
            self.health.update_health(
                is_healthy=False,
                error=str(e)
            )
            raise
            
    async def _process_requests(self) -> None:
        """Process pending requests."""
        while self._running:
            try:
                # Get pending requests
                requests = self.queue.get_pending_requests()
                
                for request in requests:
                    try:
                        response = await self.browser.send_message(request.message)
                        self.queue.update_request(
                            request.id,
                            status='completed',
                            response=response
                        )
                        self.health.update_health(
                            is_healthy=True,
                            message_count=self.health.health.message_count + 1
                        )
                    except Exception as e:
                        self.queue.update_request(
                            request.id,
                            status='failed',
                            error=str(e)
                        )
                        self.health.update_health(
                            is_healthy=False,
                            error=str(e)
                        )
                        
                # Clear completed requests
                self.queue.clear_completed()
                
                # Check browser health
                if not self.browser.is_browser_running():
                    logger.warning("Browser not running, attempting to restart")
                    await self.launch_browser()
                    
                if not self.browser.is_window_focused():
                    logger.warning("Cursor window not focused")
                    
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing requests: {e}")
                await asyncio.sleep(5)
                
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