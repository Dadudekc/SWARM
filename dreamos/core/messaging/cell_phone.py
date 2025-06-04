"""
Cell Phone Interface
------------------
Provides a simplified interface to the unified message system.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import argparse
from .base import BaseMessagingComponent
from .common import Message

from .unified_message_system import (
    MessageSystem,
    MessageMode,
    MessagePriority
)

logger = logging.getLogger('dreamos.messaging')

class CellPhone(BaseMessagingComponent):
    """Simplified interface to the unified message system."""
    
    def __init__(self, agent_id: str, ums: Any):
        """Initialize cell phone interface.
        
        Args:
            agent_id: Agent identifier
            ums: Unified message system instance
        """
        super().__init__()
        self.agent_id = agent_id
        self.ums = ums
    
    async def send_message(
        self,
        to_agent: str,
        content: str,
        mode: str = "NORMAL",
        priority: str = "NORMAL",
        from_agent: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a message.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode
            priority: Message priority
            from_agent: Sender agent ID
            metadata: Additional message metadata
            
        Returns:
            bool: True if message was successfully sent
        """
        try:
            # Convert mode and priority strings to enums
            message_mode = MessageMode[mode.upper()]
            message_priority = MessagePriority[priority.upper()]
            
            return await self.ums.send(
                to_agent=to_agent,
                content=content,
                mode=message_mode,
                priority=message_priority,
                from_agent=from_agent,
                metadata=metadata
            )
            
        except KeyError as e:
            logger.error(f"Invalid message mode or priority: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get pending messages for an agent.
        
        Args:
            agent_id: ID of agent to get messages for
            
        Returns:
            List[Dict[str, Any]]: List of pending messages
        """
        try:
            messages = await self.ums.receive(agent_id)
            return [
                {
                    "message_id": msg.message_id,
                    "from_agent": msg.from_agent,
                    "content": msg.content,
                    "mode": msg.mode.value,
                    "priority": msg.priority.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    async def get_message_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get message history.
        
        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Optional maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: List of historical messages
        """
        try:
            messages = await self.ums.get_history(
                agent_id=agent_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            return [
                {
                    "message_id": msg.message_id,
                    "from_agent": msg.from_agent,
                    "to_agent": msg.to_agent,
                    "content": msg.content,
                    "mode": msg.mode.value,
                    "priority": msg.priority.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                    "status": msg.status
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []
    
    async def subscribe(
        self,
        topic: str,
        handler: callable
    ) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
    
    async def subscribe_pattern(
        self,
        pattern: str,
        handler: callable
    ) -> None:
        """Subscribe to messages matching a pattern.
        
        Args:
            pattern: Regex pattern to match
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe_pattern(pattern, handler)
        except Exception as e:
            logger.error(f"Error subscribing to pattern {pattern}: {e}")
    
    async def unsubscribe(
        self,
        topic: str,
        handler: callable
    ) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        try:
            await self.ums.unsubscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")
    
    async def unsubscribe_pattern(
        self,
        pattern: str,
        handler: callable
    ) -> None:
        """Unsubscribe from a pattern.
        
        Args:
            pattern: Pattern to unsubscribe from
            handler: Handler to remove
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
    
    async def _process_message(self, message: Message) -> None:
        """Process a single message.
        
        Args:
            message: Message to process
        """
        try:
            await self.ums.process_message(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

async def send_message(
    to_agent: str,
    content: str,
    mode: str = "NORMAL",
    priority: str = "NORMAL",
    from_agent: str = "system",
    metadata: Optional[Dict[str, Any]] = None,
    runtime_dir: Optional[Path] = None
) -> bool:
    """Send a message using a temporary CellPhone instance.
    
    Args:
        to_agent: Target agent ID
        content: Message content
        mode: Message mode
        priority: Message priority
        from_agent: Sender agent ID
        metadata: Additional message metadata
        runtime_dir: Optional runtime directory
        
    Returns:
        bool: True if message was successfully sent
    """
    phone = CellPhone(agent_id="temp", ums=MessageSystem(runtime_dir=runtime_dir))
    try:
        return await phone.send_message(
            to_agent=to_agent,
            content=content,
            mode=mode,
            priority=priority,
            from_agent=from_agent,
            metadata=metadata
        )
    finally:
        await phone.cleanup()

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Dream.OS Cell Phone Interface")
    parser.add_argument("--to", required=True, help="Target agent ID")
    parser.add_argument("--content", required=True, help="Message content")
    parser.add_argument("--mode", default="NORMAL", help="Message mode")
    parser.add_argument("--priority", default="NORMAL", help="Message priority")
    parser.add_argument("--from-agent", default="system", help="Sender agent ID")
    parser.add_argument("--runtime-dir", help="Runtime directory")
    return parser.parse_args()

def validate_priority(priority: str) -> str:
    """Validate and normalize message priority string."""
    allowed = {p.name for p in MessagePriority}
    p = priority.upper()
    if p not in allowed:
        raise ValueError(f"Invalid priority: {priority}")
    return p

def cli_main():
    """Stub CLI entry point for cell phone interface."""
    print("CellPhone CLI not implemented. Use as a module.")

__all__ = [
    "CellPhone",
    "send_message",
    "parse_args",
    "validate_priority",
    "cli_main"
] 