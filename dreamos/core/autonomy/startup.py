"""
Autonomy System Startup
---------------------
Coordinates all autonomy components:
1. Autonomy Loop Runner
2. Midnight Runner
3. Test Watcher
4. Bridge Outbox Handler
"""

import asyncio
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..logging.log_manager import LogManager
from .autonomy_loop_runner import AutonomyLoopRunner
from .midnight_runner import MidnightRunner
from .test_watcher import TestWatcher
from .bridge_outbox_handler import BridgeOutboxHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomySystem:
    """Coordinates all autonomy components."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the autonomy system.
        
        Args:
            config_path: Optional path to config file
        """
        self.logger = LogManager()
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.autonomy_loop = AutonomyLoopRunner(self.config)
        self.midnight_runner = MidnightRunner(self.config)
        self.test_watcher = TestWatcher(self.config)
        self.bridge_handler = BridgeOutboxHandler(self.config)
        
        # Runtime state
        self.is_running = False
        self.components: List[Any] = []
        
        # Initialize logging
        self.logger.info(
            platform="autonomy_system",
            status="initialized",
            message="Autonomy system initialized",
            tags=["init", "system"]
        )
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            if not config_path:
                config_path = "config/autonomy_config.json"
            
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.warning(
                    platform="autonomy_system",
                    status="warning",
                    message=f"Config file not found: {config_path}",
                    tags=["config", "warning"]
                )
                return {}
            
            with open(config_file) as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(
                platform="autonomy_system",
                status="error",
                message=f"Error loading config: {str(e)}",
                tags=["config", "error"]
            )
            return {}
    
    async def start(self):
        """Start all autonomy components."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start components
        self.components = [
            self.autonomy_loop,
            self.midnight_runner,
            self.test_watcher,
            self.bridge_handler
        ]
        
        for component in self.components:
            await component.start()
        
        self.logger.info(
            platform="autonomy_system",
            status="started",
            message="All autonomy components started",
            tags=["start", "system"]
        )
    
    async def stop(self):
        """Stop all autonomy components."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop components in reverse order
        for component in reversed(self.components):
            await component.stop()
        
        self.logger.info(
            platform="autonomy_system",
            status="stopped",
            message="All autonomy components stopped",
            tags=["stop", "system"]
        )

async def main():
    """Main entry point."""
    # Create system
    system = AutonomySystem()
    
    # Handle signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(system.stop())
        )
    
    try:
        # Start system
        await system.start()
        
        # Keep running
        while system.is_running:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        pass
    finally:
        # Ensure clean shutdown
        await system.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass 