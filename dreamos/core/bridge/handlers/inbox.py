"""
Inbox Handler Module
-----------------
Handles incoming messages from external sources and routes them to agent mailboxes.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import BaseBridgeHandler
from ..chatgpt.bridge import ChatGPTBridge

logger = logging.getLogger(__name__)

class BridgeInboxHandler(BaseBridgeHandler):
    """Handles incoming messages from external sources and routes them to agent mailboxes."""
    
    def __init__(
        self,
        bridge: ChatGPTBridge,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the inbox handler.
        
        Args:
            bridge: ChatGPT bridge instance
            config: Optional configuration dictionary
        """
        super().__init__(bridge, None, config)
        self.mailbox_root = Path("agent_tools/mailbox")
        
    def write_response(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Write a response to an agent's mailbox.
        
        Args:
            agent_id: ID of the agent to write to
            message: Message to write
            
        Returns:
            bool: True if write was successful
        """
        try:
            # Ensure agent mailbox exists
            agent_mailbox = self.mailbox_root / f"agent-{agent_id}"
            agent_mailbox.mkdir(parents=True, exist_ok=True)
            
            # Write response
            response_path = agent_mailbox / "response.json"
            with open(response_path, "w") as f:
                json.dump(message, f, indent=2)
                
            logger.info(f"Wrote response to {response_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write response for agent {agent_id}: {e}")
            return False
            
    async def process(self, message: Dict[str, Any]) -> bool:
        """Process an incoming message.
        
        Args:
            message: Message to process
            
        Returns:
            bool: True if message was processed successfully
        """
        try:
            # Extract message data
            agent_id = message.get("recipient")
            if not agent_id:
                logger.warning("Message missing recipient field")
                return False
                
            # Validate message structure
            task_id = message.get("task_id")
            output = message.get("output")
            
            if not all([task_id, output]):
                logger.warning(f"Invalid message structure for agent {agent_id}")
                return False
                
            # Create response
            response = {
                "type": "response",
                "content": {
                    "id": task_id,
                    "data": output,
                    "sender": message.get("sender", "BridgeInboxHandler"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Write response to agent mailbox
            success = self.write_response(agent_id, response)
            if success:
                logger.info(f"Delivered response to agent {agent_id} for task {task_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False
            
    async def process_batch(self, messages: List[Dict[str, Any]]) -> bool:
        """Process a batch of incoming messages.
        
        Args:
            messages: List of messages to process
            
        Returns:
            bool: True if all messages were processed successfully
        """
        try:
            success = True
            for message in messages:
                if not await self.process(message):
                    success = False
            return success
            
        except Exception as e:
            logger.error(f"Error processing message batch: {e}")
            return False
            
    async def process_file(self, file_path: Path) -> bool:
        """Process messages from a file.
        
        Args:
            file_path: Path to file containing messages
            
        Returns:
            bool: True if file was processed successfully
        """
        try:
            # Read messages
            with open(file_path) as f:
                messages = json.load(f)
                
            if not isinstance(messages, list):
                messages = [messages]
                
            # Process messages
            success = await self.process_batch(messages)
            
            # Clear file after processing
            if success:
                with open(file_path, "w") as f:
                    json.dump([], f)
                    
            return success
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False 