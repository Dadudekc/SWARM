"""
Bridge Inbox Handler
-----------------
Processes incoming messages from bridges.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import BaseBridgeHandler
from ...utils.core_utils import (
    load_json,
    save_json,
    atomic_write,
    safe_read,
    safe_write
)

# Configure logging
logger = logging.getLogger(__name__)

class BridgeInboxHandler(BaseBridgeHandler):
    """Processes incoming messages from bridges."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge inbox handler.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(
            config=config,
            watch_dir=Path(config.get("paths", {}).get("bridge_inbox", "data/bridge_inbox")),
            file_pattern="*.json"
        )
        
        # Initialize components
        self.archive_dir = Path(self.config.get("paths", {}).get("bridge_archive", "data/bridge_archive"))
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    async def _process_items(self):
        """Process items in the handler."""
        # Check for new messages
        for file_path in self.watch_dir.glob(self.file_pattern):
            if file_path.name not in self.processed_items:
                await self._process_file(file_path)
    
    async def _process_file(self, file_path: Path):
        """Process a file.
        
        Args:
            file_path: Path to file
        """
        try:
            # Load message data
            message = await self._load_json(str(file_path))
            if not message:
                return
            
            # Process message
            await self._process_message(message)
            
            # Move to archive
            archive_path = self.archive_dir / file_path.name
            await self._move_to_archive(file_path, archive_path)
            
            # Mark as processed
            self.processed_items.add(file_path.name)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process a single message.
        
        Args:
            message: Message to process
        """
        try:
            # Extract message data
            message_type = message.get("type")
            content = message.get("content")
            metadata = message.get("metadata", {})
            
            if not all([message_type, content]):
                logger.error("Invalid message format")
                return
            
            # Process based on type
            if message_type == "response":
                await self._handle_response(content, metadata)
            elif message_type == "error":
                await self._handle_error(content, metadata)
            elif message_type == "status":
                await self._handle_status(content, metadata)
            else:
                logger.warning(f"Unknown message type: {message_type}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_response(self, content: Dict[str, Any], metadata: Dict[str, Any]):
        """Handle a response message.
        
        Args:
            content: Response content
            metadata: Response metadata
        """
        try:
            # Extract response data
            response_id = content.get("id")
            agent_id = content.get("agent_id")
            response_data = content.get("data")
            
            if not all([response_id, agent_id, response_data]):
                logger.error("Invalid response format")
                return
            
            # Process response
            # ... (response processing logic)
            
            logger.info(f"Processed response {response_id} from agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error handling response: {e}")
    
    async def _handle_error(self, content: Dict[str, Any], metadata: Dict[str, Any]):
        """Handle an error message.
        
        Args:
            content: Error content
            metadata: Error metadata
        """
        try:
            # Extract error data
            error_id = content.get("id")
            error_type = content.get("type")
            error_message = content.get("message")
            
            if not all([error_id, error_type, error_message]):
                logger.error("Invalid error format")
                return
            
            # Process error
            # ... (error processing logic)
            
            logger.error(f"Processed error {error_id}: {error_message}")
            
        except Exception as e:
            logger.error(f"Error handling error: {e}")
    
    async def _handle_status(self, content: Dict[str, Any], metadata: Dict[str, Any]):
        """Handle a status message.
        
        Args:
            content: Status content
            metadata: Status metadata
        """
        try:
            # Extract status data
            status_id = content.get("id")
            status_type = content.get("type")
            status_data = content.get("data")
            
            if not all([status_id, status_type, status_data]):
                logger.error("Invalid status format")
                return
            
            # Process status
            # ... (status processing logic)
            
            logger.info(f"Processed status {status_id}: {status_type}")
            
        except Exception as e:
            logger.error(f"Error handling status: {e}")
    
    async def _move_to_archive(self, source: Path, target: Path):
        """Move file to archive.
        
        Args:
            source: Source file path
            target: Target file path
        """
        try:
            # Ensure target directory exists
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            await atomic_write(target, await safe_read(source))
            await safe_write(source, b"")  # Clear source file
            
        except Exception as e:
            logger.error(f"Error moving file to archive: {e}") 