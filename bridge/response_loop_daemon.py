"""
Response Loop Daemon
------------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
Implements the full Cursor-ChatGPT communication loop.
"""

import json
import logging
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from watchdog.observers import Observer

from .daemon.base import BridgeResponseLoopDaemon
from .processors.prompt import PromptProcessor
from .processors.validation import ResponseValidator
from .handlers.mailbox import AgentMailboxHandler
from .monitoring import BridgeMonitor
from .discord_hook import DiscordHook, EventType
from .chatgpt_bridge_loop import ChatGPTBridgeLoop
from dreamos.core.autonomy.utils.response_utils import extract_agent_id_from_file
from .handlers.response import process_response_file, send_to_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseLoopDaemon(BridgeResponseLoopDaemon):
    """Response loop daemon implementation for Cursor-ChatGPT communication."""
    
    def __init__(self, config_path: str, discord_token: Optional[str] = None):
        """Initialize the response loop daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config_path, discord_token)
        
        # Set up paths
        self.agent_mailbox = Path(self.config["paths"]["agent_mailbox"])
        self.archive_dir = Path(self.config["paths"]["archive"])
        self.failed_dir = Path(self.config["paths"]["failed"])
        self.validated_dir = Path(self.config["paths"]["validated"])
        
        # Initialize components
        self.monitor = BridgeMonitor()
        self.discord = DiscordHook()
        self.prompt_processor = PromptProcessor('bridge/prompt_templates')
        self.validator = ResponseValidator()
        
        # Initialize ChatGPT bridge
        self.bridge = ChatGPTBridgeLoop(self.config["chatgpt"]["config_path"])
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            AgentMailboxHandler(self),
            str(self.agent_mailbox),
            recursive=False
        )
        self.observer.start()
    
    async def start(self):
        """Start the response loop daemon."""
        await super().start()
        self.bridge.run()  # Start in a separate thread
        logger.info("Response loop daemon started")
    
    async def stop(self):
        """Stop the response loop daemon."""
        self.bridge.driver.quit()  # Stop the browser
        await super().stop()
        logger.info("Response loop daemon stopped")
