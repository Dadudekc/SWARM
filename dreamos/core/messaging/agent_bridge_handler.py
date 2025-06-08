"""
Agent Bridge Handler Module

Manages communication between agents and the bridge system.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .bridge_integration import BridgeIntegration
from .response_tracker import AgentResponseTracker

logger = logging.getLogger(__name__)

class AgentBridgeHandler:
    """Handles communication between agents and the bridge system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the agent bridge handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.bridge_integration = BridgeIntegration(config)
        self.response_tracker = AgentResponseTracker(config)
        
    async def initialize(self) -> bool:
        """Initialize the bridge handler.
        
        Returns:
            True if initialization successful
        """
        try:
            # Create outbox directory
            outbox_dir = Path(self.config.get("bridge_outbox_dir", "runtime/bridge_outbox"))
            outbox_dir.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing bridge handler: {e}")
            return False
            
    async def start(self) -> bool:
        """Start the bridge handler.
        
        Returns:
            True if start successful
        """
        try:
            return True
            
        except Exception as e:
            logger.error(f"Error starting bridge handler: {e}")
            return False
            
    async def stop(self) -> bool:
        """Stop the bridge handler.
        
        Returns:
            True if stop successful
        """
        try:
            return True
            
        except Exception as e:
            logger.error(f"Error stopping bridge handler: {e}")
            return False
            
    async def handle_agent_message(self, agent_id: str, message: str) -> bool:
        """Handle a message from an agent.
        
        Args:
            agent_id: ID of the agent
            message: Message content
            
        Returns:
            True if message handled successfully
        """
        try:
            # Write to outbox
            outbox_path = Path(self.config.get("bridge_outbox_dir", "runtime/bridge_outbox")) / f"agent-{agent_id}.json"
            
            with open(outbox_path, 'w') as f:
                json.dump({
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat()
                }, f)
                
            return True
            
        except Exception as e:
            logger.error(f"Error handling message for agent {agent_id}: {e}")
            return False
            
    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get status for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary containing agent status
        """
        try:
            # Get bridge status
            bridge_status = await self.bridge_integration.get_bridge_status(agent_id)
            
            # Get response history
            history = await self.response_tracker.get_response_history(agent_id, limit=5)
            
            return {
                "bridge": bridge_status,
                "recent_responses": history
            }
            
        except Exception as e:
            logger.error(f"Error getting status for agent {agent_id}: {e}")
            return {
                "bridge": {
                    "handler_running": False,
                    "last_response": None
                },
                "recent_responses": []
            } 