"""
Bridge Response Loop Daemon
------------------------
Unified implementation of the bridge response loop daemon.
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .chatgpt.bridge import ChatGPTBridge
from .handlers.outbox import BridgeOutboxHandler
from .handlers.inbox import BridgeInboxHandler
from .processors.message import BridgeMessageProcessor
from .processors.response import BridgeResponseProcessor
from .monitoring.metrics import BridgeMetrics
from .monitoring.health import BridgeHealth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeResponseLoopDaemon:
    """Unified bridge response loop daemon."""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the daemon.
        
        Args:
            config_path: Path to config file
            config: Optional config dictionary
        """
        # Load config
        if config_path:
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            self.config = config or {}
            
        # Set up paths
        self.base_dir = Path(self.config.get("paths", {}).get("base", "data"))
        self.outbox_dir = self.base_dir / "outbox"
        self.inbox_dir = self.base_dir / "inbox"
        self.archive_dir = self.base_dir / "archive"
        self.failed_dir = self.base_dir / "failed"
        
        # Create directories
        for directory in [self.base_dir, self.outbox_dir, self.inbox_dir, self.archive_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize components
        self.bridge = ChatGPTBridge(self.config.get("bridge", {}))
        self.outbox_handler = BridgeOutboxHandler(self.bridge, self.outbox_dir)
        self.inbox_handler = BridgeInboxHandler(self.bridge, self.inbox_dir)
        self.message_processor = BridgeMessageProcessor(self.bridge)
        self.response_processor = BridgeResponseProcessor(self.bridge)
        self.metrics = BridgeMetrics()
        self.health = BridgeHealth()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # Set up state
        self.running = False
        self.tasks = []
        
    async def start(self) -> None:
        """Start the daemon."""
        try:
            logger.info("Starting bridge response loop daemon...")
            
            # Start components
            self.running = True
            self.tasks = [
                asyncio.create_task(self._run_outbox_loop()),
                asyncio.create_task(self._run_inbox_loop()),
                asyncio.create_task(self._run_health_loop())
            ]
            
            # Wait for tasks
            await asyncio.gather(*self.tasks)
            
        except Exception as e:
            logger.error(f"Error starting daemon: {e}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop the daemon."""
        try:
            logger.info("Stopping bridge response loop daemon...")
            
            # Stop components
            self.running = False
            
            # Cancel tasks
            for task in self.tasks:
                task.cancel()
                
            # Wait for tasks
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Clean up
            await self.outbox_handler.cleanup()
            await self.inbox_handler.cleanup()
            
        except Exception as e:
            logger.error(f"Error stopping daemon: {e}")
            raise
            
    def _handle_signal(self, signum: int, frame: Any) -> None:
        """Handle signals.
        
        Args:
            signum: Signal number
            frame: Frame object
        """
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.stop())
        
    async def _run_outbox_loop(self) -> None:
        """Run outbox processing loop."""
        while self.running:
            try:
                # Process outbox
                await self.outbox_handler.process()
                
                # Sleep
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in outbox loop: {e}")
                await asyncio.sleep(5)
                
    async def _run_inbox_loop(self) -> None:
        """Run inbox processing loop."""
        while self.running:
            try:
                # Process inbox
                await self.inbox_handler.process()
                
                # Sleep
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in inbox loop: {e}")
                await asyncio.sleep(5)
                
    async def _run_health_loop(self) -> None:
        """Run health check loop."""
        while self.running:
            try:
                # Update health
                await self.health.update()
                
                # Sleep
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in health loop: {e}")
                await asyncio.sleep(5)
                
def main() -> None:
    """Main entry point."""
    try:
        # Create daemon
        daemon = BridgeResponseLoopDaemon()
        
        # Run daemon
        asyncio.run(daemon.start())
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main() 