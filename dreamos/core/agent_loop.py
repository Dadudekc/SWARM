"""
Agent Loop Module

Handles the main agent execution loop.
"""

import os
import json
import time
import logging
import asyncio
import discord
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .agent_control import AgentController
from .agent_logger import AgentLogger
from .message_processor import MessageProcessor
from .persistent_queue import PersistentQueue

logger = logging.getLogger('agent_loop')

class AgentLoop:
    """Monitors agent inboxes and processes incoming prompts."""
    
    def __init__(self):
        """Initialize the agent loop."""
        self.controller = AgentController()
        self.inbox_path = Path("D:/SWARM/Dream.OS/runtime/agent_memory")
        self.processed_messages = set()
        
    def _load_inbox(self, agent_id: str) -> List[dict]:
        """Load messages from an agent's inbox.
        
        Args:
            agent_id: The agent ID to load inbox for
            
        Returns:
            List of messages in the inbox
        """
        try:
            inbox_file = self.inbox_path / agent_id / "inbox.json"
            if not inbox_file.exists():
                return []
                
            with open(inbox_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading inbox for agent {agent_id}: {e}")
            return []
            
    def _process_inbox(self, agent_id: str) -> None:
        """Process messages in an agent's inbox.
        
        Args:
            agent_id: The agent ID to process inbox for
        """
        messages = self._load_inbox(agent_id)
        for msg in messages:
            msg_id = f"{agent_id}:{msg.get('id', '')}"
            if msg_id in self.processed_messages:
                continue
                
            try:
                # Process the message
                content = msg.get('content', '')
                if content:
                    logger.info(f"Processing message for agent {agent_id}: {content[:50]}...")
                    self.controller.message_processor.send_message(agent_id, content, "NORMAL")
                    
                # Mark as processed
                self.processed_messages.add(msg_id)
                
            except Exception as e:
                logger.error(f"Error processing message for agent {agent_id}: {e}")
                
    def run(self) -> None:
        """Run the agent loop."""
        logger.info("Starting agent loop...")
        
        while True:
            try:
                # Process each agent's inbox
                for agent_id in self.controller.coordinate_manager.coordinates.keys():
                    self._process_inbox(agent_id)
                    
                # Sleep to prevent excessive CPU usage
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Agent loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                time.sleep(5)  # Longer sleep on error

def start_agent_loops() -> None:
    """Start the agent loops."""
    loop = AgentLoop()
    loop.run()

if __name__ == "__main__":
    start_agent_loops() 