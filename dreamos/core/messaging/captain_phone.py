"""
Captain Phone Interface
---------------------
Provides specialized communication for the captain to interact with agents.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import time
import yaml
import json

from .cell_phone import CellPhone
from .message_system import MessageRecord, MessageMode

logger = logging.getLogger('dreamos.messaging.captain_phone')

class CaptainPhone(CellPhone):
    """Special phone interface for the captain to communicate with agents."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the captain's phone.
        
        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)
        
        # Load captain-specific config
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                captain_config = config.get('captain', {})
        else:
            captain_config = {}
        
        # Set captain-specific settings
        self.captain_id = captain_config.get('id', 'Captain')
        self.response_timeout = captain_config.get('response_timeout', 30)
        self.response_dir = Path(captain_config.get('response_dir', 'responses'))
        self.response_dir.mkdir(exist_ok=True)
        
        logger.info(
            platform="captain_phone",
            status="initialized",
            message="Captain's phone initialized",
            tags=["init"]
        )
    
    def send_message(
        self,
        to_agent: str,
        content: str,
        mode: str = "NORMAL",
        priority: int = 0,
        wait_for_response: bool = True
    ) -> bool:
        """Send a message from the captain to an agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode (NORMAL, PRIORITY, BULK, etc.)
            priority: Message priority (0-5)
            wait_for_response: Whether to wait for agent response
            
        Returns:
            bool: True if message was sent successfully and response received (if waiting)
        """
        try:
            # Send the message
            success = super().send_message(
                to_agent=to_agent,
                content=content,
                mode=mode,
                priority=priority,
                from_agent=self.captain_id
            )
            
            if not success:
                return False
            
            # If not waiting for response, we're done
            if not wait_for_response:
                return True
            
            # Monitor for response
            return self._monitor_response(to_agent)
            
        except Exception as e:
            logger.error(
                platform="captain_phone",
                status="error",
                message=f"Error sending message: {str(e)}",
                tags=["message", "error"]
            )
            return False
    
    def _monitor_response(self, to_agent: str) -> bool:
        """Monitor for agent response with timeout.
        
        Args:
            to_agent: ID of agent to monitor
            
        Returns:
            bool: True if response received within timeout
        """
        start_time = time.time()
        last_message_count = len(self.get_message_history())
        
        while time.time() - start_time < self.response_timeout:
            # Check for new messages
            history = self.get_message_history()
            if len(history) > last_message_count:
                # Found a response
                response = history[-1]
                if response.sender_id == to_agent:
                    # Save the response
                    self._save_response(to_agent, response)
                    return True
            
            time.sleep(0.5)  # Check every half second
        
        logger.warning(
            platform="captain_phone",
            status="timeout",
            message=f"Response timeout for {to_agent}",
            tags=["message", "timeout"]
        )
        return False
    
    def _save_response(self, agent_id: str, response: MessageRecord) -> None:
        """Save agent response to file.
        
        Args:
            agent_id: ID of responding agent
            response: Response message record
        """
        try:
            # Create response file
            response_file = self.response_dir / f"{agent_id}_{response.timestamp.isoformat()}.json"
            
            # Save response data
            response_data = {
                "agent_id": agent_id,
                "timestamp": response.timestamp.isoformat(),
                "content": response.content,
                "mode": response.mode.name,
                "metadata": response.metadata
            }
            
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.info(
                platform="captain_phone",
                status="saved",
                message=f"Saved response from {agent_id}",
                tags=["message", "save"]
            )
            
        except Exception as e:
            logger.error(
                platform="captain_phone",
                status="error",
                message=f"Error saving response: {str(e)}",
                tags=["message", "error"]
            )
    
    def broadcast_message(
        self,
        content: str,
        mode: str = "NORMAL",
        priority: int = 0,
        exclude_agents: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Broadcast a message to all agents.
        
        Args:
            content: Message content
            mode: Message mode
            priority: Message priority
            exclude_agents: List of agent IDs to exclude
            
        Returns:
            Dict[str, bool]: Map of agent IDs to success status
        """
        try:
            # Get list of all agents
            all_agents = self._get_all_agents()
            
            # Filter out excluded agents
            if exclude_agents:
                target_agents = [a for a in all_agents if a not in exclude_agents]
            else:
                target_agents = all_agents
            
            # Send to each agent
            results = {}
            for agent_id in target_agents:
                success = self.send_message(
                    to_agent=agent_id,
                    content=content,
                    mode=mode,
                    priority=priority,
                    wait_for_response=False  # Don't wait for responses in broadcast
                )
                results[agent_id] = success
            
            return results
            
        except Exception as e:
            logger.error(
                platform="captain_phone",
                status="error",
                message=f"Error broadcasting message: {str(e)}",
                tags=["message", "error"]
            )
            return {}
    
    def _get_all_agents(self) -> List[str]:
        """Get list of all active agents.
        
        Returns:
            List[str]: List of agent IDs
        """
        # TODO: Implement agent discovery
        # For now, return a hardcoded list
        return ["Agent-1", "Agent-2", "Agent-3"] 