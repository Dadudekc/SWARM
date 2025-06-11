"""
Bridge Inbox Handler
-----------------
Handles incoming messages in the bridge system.
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set
from dreamos.core.bridge.base.handler import BaseHandler
from dreamos.core.bridge.base.monitor import BridgeMonitor
from dreamos.core.bridge.validation.validator import BridgeValidator

logger = logging.getLogger(__name__)

class BridgeInboxHandler(BaseHandler):
    """Handles incoming messages in the bridge system."""
    
    def __init__(self, watch_dir: Path, file_pattern: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the inbox handler.
        
        Args:
            watch_dir: Directory to watch for new messages
            file_pattern: Pattern to match message files
            config: Optional configuration dictionary
        """
        super().__init__(watch_dir, file_pattern, config)
        self.validator = BridgeValidator(config)
        self.monitor = BridgeMonitor(config)
        self.processed_items: Set[str] = set()
        
    async def process_file(self, file_path: Path) -> None:
        """Process a message file.
        
        Args:
            file_path: Path to message file
        """
        try:
            # Read and validate message
            with open(file_path, 'r') as f:
                message = json.load(f)
                
            if not await self.validator.validate(message):
                await self.monitor.update_metrics(False, ValueError(f"Invalid message format in {file_path}"))
                raise ValueError(f"Invalid message format in {file_path}")
                
            # Process message
            if message['type'] == 'response':
                await self._process_response(message)
            elif message['type'] == 'error':
                await self._process_error(message)
            else:
                await self.monitor.update_metrics(False, ValueError(f"Unknown message type: {message['type']}"))
                raise ValueError(f"Unknown message type: {message['type']}")
                
            # Mark as processed
            self.processed_items.add(file_path.name)
            await self.monitor.update_metrics(True)
            
            # Remove file
            file_path.unlink()
            
        except Exception as e:
            await self.handle_error(e, file_path)
            
    async def _process_response(self, message: Dict[str, Any]) -> None:
        """Process a response message.
        
        Args:
            message: Response message to process
        """
        logger.info("Processing response message")
        content = message['content']
        logger.info(f"Received response for task {content['id']} from {content['sender']}")
        
    async def _process_error(self, message: Dict[str, Any]) -> None:
        """Process an error message.
        
        Args:
            message: Error message to process
        """
        logger.info("Processing error message")
        content = message['content']
        logger.error(f"Received error: {content['error']}")
        
    async def handle_error(self, error: Exception, file_path: Path) -> None:
        """Handle processing error.
        
        Args:
            error: Error that occurred
            file_path: Path to file that caused error
        """
        logger.error(f"Error processing {file_path}: {str(error)}")
        
        # Move file to error directory
        error_dir = Path(self.config['error_dir'])
        error_dir.mkdir(parents=True, exist_ok=True)
        error_path = error_dir / file_path.name
        
        try:
            shutil.move(str(file_path), str(error_path))
        except Exception as e:
            logger.error(f"Failed to move file to error directory: {str(e)}")
            
    async def cleanup(self) -> None:
        """Clean up handler state."""
        self.processed_items.clear()
        await self.monitor.reset()
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get handler metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.monitor.get_metrics() 