"""
Cursor Agent Bridge
-----------------
Handles automated response collection and feedback loops between Cursor AI agents and ChatGPT.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pyautogui
import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..bridge.chatgpt.bridge import ChatGPTBridge
from ..agent_control.response_capture import ResponseCapture
from ..agent_control.ui_automation import UIAutomation
from ..utils.core_utils import load_json, save_json, atomic_write

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CursorAgentBridge:
    """Handles automated response collection and feedback loops."""
    
    def __init__(self, config_path: str):
        """Initialize the Cursor agent bridge.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_json(config_path)
        
        # Initialize components
        self.chatgpt_bridge = ChatGPTBridge(self.config)
        self.response_capture = ResponseCapture()
        self.ui_automation = UIAutomation(config_path)
        
        # Set up directories
        self.bridge_outbox = Path(self.config["paths"]["bridge_outbox"])
        self.bridge_outbox.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.agent_regions = {}
        self._load_agent_regions()
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            BridgeOutboxHandler(self),
            str(self.bridge_outbox),
            recursive=False
        )
        self.observer.start()
        
    def _load_agent_regions(self):
        """Load agent screen regions from config."""
        try:
            regions_path = Path(self.config["paths"]["runtime"]) / "agent_regions.json"
            if regions_path.exists():
                self.agent_regions = load_json(str(regions_path))
        except Exception as e:
            logger.error(f"Error loading agent regions: {e}")
            
    async def start(self):
        """Start the bridge service."""
        try:
            await self.chatgpt_bridge.initialize()
            logger.info("Cursor agent bridge started")
        except Exception as e:
            logger.error(f"Error starting bridge: {e}")
            raise
            
    async def stop(self):
        """Stop the bridge service."""
        try:
            self.observer.stop()
            self.observer.join()
            await self.chatgpt_bridge.cleanup()
            logger.info("Cursor agent bridge stopped")
        except Exception as e:
            logger.error(f"Error stopping bridge: {e}")
            
    async def process_agent_response(self, agent_id: str) -> Optional[str]:
        """Process a response from a Cursor agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Captured response text if successful
        """
        try:
            # 1. Capture response from screen
            if agent_id not in self.agent_regions:
                logger.error(f"No region found for agent {agent_id}")
                return None
                
            region = self.agent_regions[agent_id]
            response = self.response_capture.capture_response(agent_id)
            
            if not response:
                logger.warning(f"No response captured for agent {agent_id}")
                return None
                
            # 2. Save to bridge outbox
            outbox_path = self.bridge_outbox / f"agent-{agent_id}.json"
            save_json({
                "status": "complete",
                "response": response,
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            }, str(outbox_path))
            
            # 3. Send to ChatGPT
            chatgpt_response = await self.chatgpt_bridge.send_message(response)
            
            # 4. Inject response back to Cursor
            self._inject_to_cursor(agent_id, chatgpt_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing agent response: {e}")
            return None
            
    def _inject_to_cursor(self, agent_id: str, response: str):
        """Inject response into Cursor window.
        
        Args:
            agent_id: ID of the agent
            response: Response to inject
        """
        try:
            if agent_id not in self.agent_regions:
                logger.error(f"No region found for agent {agent_id}")
                return
                
            region = self.agent_regions[agent_id]
            
            # Calculate input box position
            input_x = region["top_left"]["x"] + 50  # Approximate input box position
            input_y = region["bottom_right"]["y"] - 50
            
            # Click input box and type response
            pyautogui.click(input_x, input_y)
            pyautogui.write(response)
            pyautogui.press('enter')
            
        except Exception as e:
            logger.error(f"Error injecting to Cursor: {e}")
            
    async def monitor_agent(self, agent_id: str):
        """Monitor an agent for responses.
        
        Args:
            agent_id: ID of the agent to monitor
        """
        while True:
            try:
                # Check for response
                response = await self.process_agent_response(agent_id)
                
                if response:
                    logger.info(f"Processed response from agent {agent_id}")
                    
                # Wait before next check
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error monitoring agent {agent_id}: {e}")
                await asyncio.sleep(5)

class BridgeOutboxHandler(FileSystemEventHandler):
    """Handles file creation events in bridge outbox."""
    
    def __init__(self, bridge: CursorAgentBridge):
        """Initialize the handler.
        
        Args:
            bridge: Bridge instance
        """
        self.bridge = bridge
        
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith('.json'):
            return
            
        # Extract agent ID from filename
        agent_id = Path(event.src_path).stem.split('-')[1]
        
        # Process response
        asyncio.create_task(
            self.bridge.process_agent_response(agent_id)
        ) 