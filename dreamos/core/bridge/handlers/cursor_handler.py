"""
Cursor Bridge Handler
------------------
Handles communication between agents and the Cursor IDE.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from dreamos.bridge_clients.cursor import CursorBridge
from dreamos.core.bridge.base import BridgeHandler
from dreamos.core.bridge.monitoring import BridgeMonitor
from dreamos.core.bridge.validation import BridgeValidator
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.json_utils import load_json, save_json

logger = logging.getLogger(__name__)

class CursorBridgeHandler(BaseHandler):
    """Handles communication between agents and the Cursor IDE."""
    
    def __init__(
        self,
        watch_dir: Path,
        file_pattern: str = "*.json",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the Cursor bridge handler.
        
        Args:
            watch_dir: Directory to watch for messages
            file_pattern: Pattern to match message files
            config: Optional configuration dictionary
        """
        super().__init__(watch_dir, file_pattern, config)
        self.logger = logging.getLogger(__name__)
        self.bridge = CursorBridge()
        self.validator = BridgeValidator(config)
        self.monitor = BridgeMonitor(config)
        self.processed_items: set[str] = set()
        
    async def start(self):
        """Start the bridge handler.
        
        This method:
        1. Starts the bridge monitor
        2. Initializes the bridge
        3. Starts the bridge
        """
        self.logger.info("Starting Cursor bridge handler")
        self.monitor.start()
        await self.bridge.start()
        self.logger.info("Cursor bridge handler started")
        
    async def stop(self):
        """Stop the bridge handler.
        
        This method:
        1. Stops the bridge
        2. Stops the bridge monitor
        3. Cleans up any resources
        """
        self.logger.info("Stopping Cursor bridge handler")
        await self.bridge.stop()
        self.monitor.stop()
        self.logger.info("Cursor bridge handler stopped")
        
    async def process_file(self, file_path: Path) -> None:
        """Process a message file.
        
        Args:
            file_path: Path to message file
        """
        try:
            # Read message
            with open(file_path, "r") as f:
                message = json.load(f)
                
            # Validate message
            if not await self.validator.validate(message):
                logger.error(f"Invalid message format in {file_path}")
                return
                
            # Process message
            response = await self.bridge.send_message(
                message.get("content", ""),
                metadata=message.get("metadata", {})
            )
            
            # Write response
            response_file = file_path.parent / f"{file_path.stem}_response.json"
            with open(response_file, "w") as f:
                json.dump({
                    "type": "response",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "source": "cursor_bridge",
                        "original_file": str(file_path)
                    }
                }, f, indent=2)
                
            # Update metrics
            self.monitor.record_metric("messages_processed", 1)
            self.processed_items.add(str(file_path))
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.monitor.record_metric("processing_errors", 1)
            
    async def handle_error(self, error: Exception, file_path: Path) -> None:
        """Handle an error.
        
        Args:
            error: Error that occurred
            file_path: Path to file that caused error
        """
        logger.error(f"Error processing {file_path}: {error}")
        self.monitor.record_metric("errors", 1)
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.stop()
        self.processed_items.clear() 