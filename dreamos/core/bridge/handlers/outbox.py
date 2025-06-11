"""
Outbox Handler Module
------------------
Handles outgoing messages for the bridge system using agent-local mailboxes.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseBridgeHandler
from ..chatgpt.bridge import ChatGPTBridge

logger = logging.getLogger(__name__)

class BridgeOutboxHandler(BaseBridgeHandler):
    """Handles outgoing messages for the bridge system using agent-local mailboxes."""
    
    def __init__(
        self,
        bridge: ChatGPTBridge,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the outbox handler.
        
        Args:
            bridge: ChatGPT bridge instance
            config: Optional configuration dictionary
        """
        # Get directory from config or use default
        directory = Path(config.get("paths", {}).get("outbox", "agent_tools/outbox")) if config else Path("agent_tools/outbox")
        
        # Get mailbox root from config
        mailbox_root = Path(config.get("paths", {}).get("mailbox", "agent_tools/mailbox")) if config else Path("agent_tools/mailbox")
        
        # Initialize base handler with paths
        handler_config = {
            **config,
            "paths": {
                "outbox": str(directory),
                "mailbox": str(mailbox_root),
                "archive": str(Path(config.get("paths", {}).get("archive", "archive"))),
                "failed": str(Path(config.get("paths", {}).get("failed", "failed")))
            }
        }
        super().__init__(bridge, directory, handler_config)
        self.mailbox_root = mailbox_root
        
        # Initialize metrics
        self.processed_messages = 0
        self.errors = {}
        self.last_error = None
        self.last_processed = None
        
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
            
    async def _process_message(self, message: Dict[str, Any]):
        """Process an outgoing message.
        
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
            if message_type == "request":
                await self._handle_request(content, metadata)
            elif message_type == "response":
                await self._handle_response(content, metadata)
            elif message_type == "error":
                await self._handle_error(content, metadata)
            elif message_type == "status":
                await self._handle_status(content, metadata)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
            # Update metrics
            self.processed_messages += 1
            self.last_processed = datetime.now()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    async def _handle_request(self, content: Dict[str, Any], metadata: Dict[str, Any]):
        """Handle a request message.
        
        Args:
            content: Request content
            metadata: Request metadata
        """
        try:
            # Extract request data
            request_id = content.get("id")
            agent_id = content.get("agent_id")
            prompt = content.get("prompt")
            
            if not all([request_id, agent_id, prompt]):
                logger.error("Invalid request format")
                return
                
            # Send to ChatGPT
            response = await self.bridge.send_message(prompt)
            
            # Write response to agent mailbox
            self.write_response(
                agent_id,
                {
                    "type": "response",
                    "content": {
                        "id": request_id,
                        "data": response,
                        "timestamp": metadata.get("timestamp")
                    }
                }
            )
            
            logger.info(f"Processed request {request_id} from agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            
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
                
            # Write response to agent mailbox
            self.write_response(
                agent_id,
                {
                    "type": "response",
                    "content": {
                        "id": response_id,
                        "data": response_data,
                        "timestamp": metadata.get("timestamp")
                    }
                }
            )
            
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
            agent_id = content.get("agent_id")
            error_type = content.get("type")
            error_message = content.get("message")
            
            if not all([error_id, agent_id, error_type, error_message]):
                logger.error("Invalid error format")
                return
                
            # Write error to agent mailbox
            self.write_response(
                agent_id,
                {
                    "type": "error",
                    "content": {
                        "id": error_id,
                        "type": error_type,
                        "message": error_message,
                        "timestamp": metadata.get("timestamp")
                    }
                }
            )
            
            logger.error(f"Processed error {error_id} for agent {agent_id}: {error_message}")
            
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
            agent_id = content.get("agent_id")
            status_data = content.get("data")
            
            if not all([status_id, agent_id, status_data]):
                logger.error("Invalid status format")
                return
                
            # Write status to agent mailbox
            self.write_response(
                agent_id,
                {
                    "type": "status",
                    "content": {
                        "id": status_id,
                        "data": status_data,
                        "timestamp": metadata.get("timestamp")
                    }
                }
            )
            
            logger.info(f"Processed status {status_id} from agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error handling status: {e}")

    async def start(self) -> bool:
        """Start the handler.
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Create directories
            self.mailbox_root.mkdir(parents=True, exist_ok=True)
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            self.failed_dir.mkdir(parents=True, exist_ok=True)
            
            # Start monitoring
            self.observer.start()
            return True
            
        except Exception as e:
            logger.error(f"Error starting handler: {e}")
            return False

    async def process(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Process a message for an agent.
        
        Args:
            agent_id: ID of the agent
            message: Message to process
            
        Returns:
            bool: True if processed successfully
        """
        try:
            # Write message to outbox
            outbox_path = self.mailbox_root / f"agent-{agent_id}" / "outbox.json"
            outbox_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(outbox_path, 'w') as f:
                json.dump(message, f, indent=2)
                
            # Process message
            await self._process_message(message)
            return True
            
        except Exception as e:
            logger.error(f"Error processing message for agent {agent_id}: {e}")
            return False

    async def _handle_error(self, message: Dict[str, Any], error: Exception) -> None:
        """Handle error messages."""
        error_response = {
            "type": "error",
            "content": {
                "error": str(error),
                "message": message
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "bridge_outbox_handler"
            }
        }
        await self.write_response(message["content"]["agent_id"], error_response)

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for this handler."""
        return {
            "processed_messages": self.processed_messages,
            "errors": self.errors,
            "last_error": str(self.last_error) if self.last_error else None,
            "last_processed": self.last_processed.isoformat() if self.last_processed else None
        } 