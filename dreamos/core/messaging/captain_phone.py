"""
Captain Phone Interface
---------------------
Provides specialized communication for the captain to interact with agents.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import time
import yaml
import json
import os

from .cell_phone import CellPhone
from .message_system import MessageRecord, MessageMode
from agent_tools.mailbox.message_handler import MessageHandler

logger = logging.getLogger('dreamos.messaging.captain_phone')

class CaptainPhone:
    """Captain phone for managing agent communications."""
    
    _instance = None
    
    def __new__(cls, config: Dict):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict):
        """Initialize captain phone.
        
        Args:
            config: Configuration dictionary containing:
                - message_handler: MessageHandler instance
                - agent_id: Captain agent ID
                - response_timeout: Optional timeout for responses (default: 30)
                - response_dir: Optional directory for responses (default: responses)
        """
        if not hasattr(self, 'initialized'):
            self.message_handler = config.get('message_handler')
            if not self.message_handler:
                raise ValueError("message_handler is required in config")
                
            self.agent_id = config.get('agent_id')
            if not self.agent_id:
                raise ValueError("agent_id is required in config")
            
            # Set default values
            self.response_timeout = config.get('response_timeout', 30)
            self.response_dir = Path(config.get('response_dir', 'responses'))
            self.response_dir.mkdir(exist_ok=True)
                
            logger.info("Cell phone initialized for agent %s", self.agent_id)
            self.initialized = True
    
    @classmethod
    def reset_singleton(cls):
        """Reset singleton instance."""
        cls._instance = None
    
    def send_message(self, to_agent: str, content: str, metadata: Optional[Dict] = None, mode: Optional[str] = None, priority: Optional[str] = None) -> bool:
        """Send message to agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            metadata: Optional message metadata
            mode: Optional message mode
            priority: Optional message priority
        Returns:
            bool: True if message sent successfully
        """
        if not content or not to_agent:
            return False
        try:
            return self.message_handler.send_message(
                to_agent=to_agent,
                content=content,
                from_agent=self.agent_id,
                metadata=metadata or {},
                mode=mode,
                priority=priority
            )
        except Exception as e:
            logger.error("Error sending message: %s", str(e))
            return False
    
    def broadcast_message(self, content: str, metadata: Optional[Dict] = None, mode: Optional[str] = None, priority: Optional[str] = None) -> bool:
        """Broadcast message to all agents.
        
        Args:
            content: Message content
            metadata: Optional message metadata
            mode: Optional message mode
            priority: Optional message priority
        Returns:
            bool: True if message broadcast successfully
        """
        if not content:
            return False
        try:
            return self.message_handler.broadcast_message(
                content=content,
                from_agent=self.agent_id,
                metadata=metadata or {},
                mode=mode,
                priority=priority
            )
        except Exception as e:
            logger.error("Error broadcasting message: %s", str(e))
            return False
    
    def get_messages(self, agent_id: str) -> List[Dict]:
        """Get messages for agent.
        
        Args:
            agent_id: Agent ID to get messages for
            
        Returns:
            List[Dict]: List of messages
        """
        try:
            return self.message_handler.get_messages(agent_id)
        except Exception as e:
            logger.error("Error getting messages: %s", str(e))
            return []
    
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge message receipt.
        
        Args:
            message_id: ID of message to acknowledge
            
        Returns:
            bool: True if message acknowledged successfully
        """
        try:
            return self.message_handler.acknowledge_message(message_id)
        except Exception as e:
            logger.error("Error acknowledging message: %s", str(e))
            return False

    def _monitor_response(self, to_agent: str) -> bool:
        """Monitor for agent response with timeout.
        
        Args:
            to_agent: ID of agent to monitor
            
        Returns:
            bool: True if response received within timeout
        """
        start_time = time.time()
        last_message_count = len(self.get_messages(to_agent))
        
        while time.time() - start_time < self.response_timeout:
            # Check for new messages
            history = self.get_messages(to_agent)
            if len(history) > last_message_count:
                # Found a response
                response = history[-1]
                if response.get("from_agent") == to_agent:  # Changed from self.agent_id to to_agent
                    # Save the response
                    self._save_response(to_agent, response)
                    return True
            
            time.sleep(0.5)  # Check every half second
        
        logger.warning("Response timeout for %s", to_agent)
        return False
    
    def _save_response(self, agent_id: str, response: Dict) -> None:
        """Save agent response to file.
        
        Args:
            agent_id: ID of responding agent
            response: Response message record
        """
        try:
            # Create response file
            response_file = self.response_dir / f"{agent_id}_{response.get('timestamp', 'unknown')}.json"
            
            # Save response data
            response_data = {
                "agent_id": agent_id,
                "timestamp": response.get('timestamp'),
                "content": response.get('content'),
                "mode": response.get('mode'),
                "metadata": response.get('metadata', {})
            }
            
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.info("Saved response from %s", agent_id)
            
        except Exception as e:
            logger.error("Error saving response: %s", str(e))
    
    def _get_all_agents(self) -> List[str]:
        """Get list of all active agents.
        
        Returns:
            List[str]: List of agent IDs
        """
        try:
            # For testing, return a fixed list of agents
            if hasattr(self, 'test_mode') and self.test_mode:
                return [f"agent-{i}" for i in range(1, 9)]  # Hardcoded 8 agents
            
            coords_file = Path("config/cursor_agent_coords.json")
            if coords_file.exists():
                with open(coords_file, "r") as f:
                    data = json.load(f)
                return [a for a in data.keys() if a != "global_ui"]

            config_file = Path("config/agent_config.yaml")
            if config_file.exists():
                with open(config_file, "r") as f:
                    cfg = yaml.safe_load(f) or {}
                if "channel_assignments" in cfg:
                    return list(cfg["channel_assignments"].keys())

            return []
        except Exception as e:
            logger.error("Agent discovery failed: %s", str(e))
            return []

    def clear_messages(self) -> bool:
        """Clear all messages for this agent."""
        try:
            return self.message_handler.clear_messages(self.agent_id)
        except Exception as e:
            logger.error("Error clearing messages: %s", str(e))
            return False
