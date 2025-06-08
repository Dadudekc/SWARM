"""
Response Loop Daemon
-----------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .handlers.bridge import BridgeHandler
from ...utils.core_utils import (
    load_json,
    save_json,
    atomic_write,
    safe_read,
    safe_write
)

# Configure logging
logger = logging.getLogger(__name__)

class ResponseLoopDaemon:
    """Monitors agent responses and generates new prompts for the ChatGPT bridge."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the response loop daemon.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.bridge = BridgeHandler(config)
        
        # Set up paths
        self.runtime_dir = Path(self.config.get("paths", {}).get("runtime", "data/runtime"))
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Load state
        self.state_file = self.runtime_dir / "response_loop_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load daemon state from file.
        
        Returns:
            Dict containing daemon state
        """
        try:
            if self.state_file.exists():
                return load_json(str(self.state_file))
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}
    
    def _save_state(self):
        """Save daemon state to file."""
        try:
            save_json(str(self.state_file), self.state)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    async def start(self):
        """Start the response loop daemon."""
        try:
            logger.info("Starting response loop daemon...")
            
            # Start bridge handler
            await self.bridge.start()
            
            # Update state
            self.state["started_at"] = datetime.now().isoformat()
            self._save_state()
            
            logger.info("Response loop daemon started")
            
        except Exception as e:
            logger.error(f"Error starting daemon: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the response loop daemon."""
        try:
            logger.info("Stopping response loop daemon...")
            
            # Stop bridge handler
            await self.bridge.stop()
            
            # Update state
            self.state["stopped_at"] = datetime.now().isoformat()
            self._save_state()
            
            logger.info("Response loop daemon stopped")
            
        except Exception as e:
            logger.error(f"Error stopping daemon: {e}")
    
    async def run(self):
        """Run the response loop daemon."""
        try:
            # Start daemon
            await self.start()
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await self.stop()
            
        except Exception as e:
            logger.error(f"Error in daemon: {e}")
            await self.stop()
    
    @classmethod
    async def create_and_run(cls, config: Optional[Dict[str, Any]] = None):
        """Create and run a response loop daemon.
        
        Args:
            config: Optional configuration dictionary
        """
        daemon = cls(config)
        await daemon.run() 