"""
Response Loop Daemon Module
------------------------
Monitors agent mailboxes and processes incoming messages.
"""

import asyncio
import glob
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .handlers.outbox import BridgeOutboxHandler
from .chatgpt.bridge import ChatGPTBridge

logger = logging.getLogger(__name__)

class ResponseLoopDaemon:
    """Daemon that monitors agent mailboxes and processes messages."""
    
    def __init__(
        self,
        bridge: ChatGPTBridge,
        poll_interval: float = 1.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the response loop daemon.
        
        Args:
            bridge: ChatGPT bridge instance
            poll_interval: Time between mailbox checks in seconds
            config: Optional configuration dictionary
        """
        self.poll_interval = poll_interval
        self.handler = BridgeOutboxHandler(bridge, config)
        self.mailbox_root = Path("agent_tools/mailbox")
        
    async def run(self):
        """Run the daemon loop."""
        logger.info("Starting response loop daemon")
        
        while True:
            try:
                # Find all agent inboxes
                inbox_files = glob.glob(str(self.mailbox_root / "agent-*/inbox.json"))
                
                for inbox_path in inbox_files:
                    agent_id = Path(inbox_path).parts[-2]
                    try:
                        # Read messages
                        with open(inbox_path, "r") as f:
                            messages = json.load(f)
                            
                        if not messages:
                            continue
                            
                        # Process each message
                        for msg in messages:
                            await self.handler._process_message(msg)
                            
                        # Clear inbox after processing
                        with open(inbox_path, "w") as f:
                            json.dump([], f)
                            
                        logger.info(f"Processed {len(messages)} messages for agent {agent_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process {inbox_path}: {e}")
                        
                # Wait before next check
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                await asyncio.sleep(self.poll_interval)
                
    async def process_messages(self, messages: List[Dict[str, Any]]) -> bool:
        """Process a list of messages.
        
        Args:
            messages: List of messages to process
            
        Returns:
            bool: True if all messages were processed successfully
        """
        try:
            for msg in messages:
                await self.handler._process_message(msg)
            return True
            
        except Exception as e:
            logger.error(f"Error processing messages: {e}")
            return False 