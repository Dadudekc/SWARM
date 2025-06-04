"""
Phone interfaces for Dream.OS.
Provides communication interfaces for different agent types.
"""

import logging
import asyncio
import time
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable
from datetime import datetime

from .unified_message_system import UnifiedMessageSystem
from .common import Message
from .enums import MessageMode, MessagePriority, MessageType

logger = logging.getLogger("dreamos.messaging.phones")

class Phone:
    """Base phone interface for agent communication."""
    
    def __init__(self, runtime_dir: Optional[Path] = None):
        """Initialize phone interface.
        
        Args:
            runtime_dir: Optional runtime directory
        """
        self.ums = UnifiedMessageSystem.instance()
        self.runtime_dir = runtime_dir
        self.agent_id = "system"
    
    async def send_message(
        self,
        to_agent: str,
        content: str,
        mode: Union[str, MessageMode] = MessageMode.NORMAL,
        priority: Union[str, int, MessagePriority] = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a message.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode
            priority: Message priority
            metadata: Additional message metadata
            
        Returns:
            bool: True if message was successfully sent
        """
        try:
            # Validate recipient
            if not to_agent or not isinstance(to_agent, str):
                raise ValueError("Agent name must be a non-empty string")
            
            # Validate content
            if not content or not isinstance(content, str):
                raise ValueError("Message content must be a non-empty string")
            
            # Convert/validate mode
            if isinstance(mode, str):
                mode = MessageMode[mode.upper()]
            
            # Convert/validate priority
            if isinstance(priority, int):
                priority = MessagePriority(priority)
            elif isinstance(priority, str):
                priority = MessagePriority[priority.upper()]
            
            return await self.ums.send(
                to_agent=to_agent,
                content=content,
                mode=mode,
                priority=priority,
                from_agent=self.agent_id,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Get pending messages.
        
        Returns:
            List[Dict[str, Any]]: List of pending messages
        """
        try:
            messages = await self.ums.receive(self.agent_id)
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    async def get_message_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get message history.
        
        Args:
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Optional maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: List of historical messages
        """
        try:
            messages = await self.ums.get_history(
                agent_id=self.agent_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
    
    async def subscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Subscribe to messages matching a pattern.
        
        Args:
            pattern: Regex pattern to match
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe_pattern(pattern, handler)
        except Exception as e:
            logger.error(f"Error subscribing to pattern {pattern}: {e}")
    
    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Callback function to remove
        """
        try:
            await self.ums.unsubscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
    
    async def unsubscribe_pattern(self, pattern: str, handler: Callable) -> None:
        """Unsubscribe from messages matching a pattern.
        
        Args:
            pattern: Regex pattern to match
            handler: Callback function to remove
        """
        try:
            await self.ums.unsubscribe_pattern(pattern, handler)
        except Exception as e:
            logger.error(f"Error unsubscribing from pattern {pattern}: {e}")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.ums.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

class CaptainPhone(Phone):
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
        self.agent_id = captain_config.get('id', 'Captain')
        self.response_timeout = captain_config.get('response_timeout', 30)
        self.response_dir = Path(captain_config.get('response_dir', 'responses'))
        self.response_dir.mkdir(exist_ok=True)
        
        logger.info("Captain's phone initialized")
    
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
            mode: Message mode
            priority: Message priority
            wait_for_response: Whether to wait for agent response
            
        Returns:
            bool: True if message was sent successfully and response received (if waiting)
        """
        try:
            # Send the message using the async interface
            success = asyncio.run(
                super().send_message(
                    to_agent=to_agent,
                    content=content,
                    mode=mode,
                    priority=priority
                )
            )
            
            if not success or not wait_for_response:
                return success
            
            # Monitor for response
            return self._monitor_response(to_agent)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _monitor_response(self, to_agent: str) -> bool:
        """Monitor for agent response with timeout.
        
        Args:
            to_agent: ID of agent to monitor
            
        Returns:
            bool: True if response received within timeout
        """
        start_time = time.time()
        last_message_count = len(asyncio.run(self.get_message_history()))
        
        while time.time() - start_time < self.response_timeout:
            # Check for new messages
            history = asyncio.run(self.get_message_history())
            if len(history) > last_message_count:
                # Found a response
                response = history[-1]
                if response.get("from_agent") == to_agent:
                    # Save the response
                    self._save_response(to_agent, response)
                    return True
            
            time.sleep(0.5)  # Check every half second
        
        logger.warning(f"Response timeout for {to_agent}")
        return False
    
    def _save_response(self, agent_id: str, response: Dict[str, Any]) -> None:
        """Save agent response to file.
        
        Args:
            agent_id: ID of responding agent
            response: Response message record
        """
        try:
            # Create response file
            response_file = self.response_dir / f"{agent_id}_{response['timestamp']}.json"
            
            # Save response data
            response_data = {
                "agent_id": agent_id,
                "timestamp": response["timestamp"],
                "content": response["content"],
                "mode": response["mode"],
                "metadata": response.get("metadata")
            }
            
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.info(f"Saved response from {agent_id}")
            
        except Exception as e:
            logger.error(f"Error saving response: {e}")
    
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
            if exclude_agents:
                all_agents = [a for a in all_agents if a not in exclude_agents]
            
            # Send message to each agent
            results = {}
            for agent_id in all_agents:
                results[agent_id] = self.send_message(
                    to_agent=agent_id,
                    content=content,
                    mode=mode,
                    priority=priority,
                    wait_for_response=False
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return {}
    
    def _get_all_agents(self) -> List[str]:
        """Get list of all active agents.
        
        Returns:
            List[str]: List of agent IDs
        """
        # TODO: Implement agent discovery
        return ["Agent-1", "Agent-2", "Agent-3"]  # Placeholder 