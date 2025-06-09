"""
Discord Bot Agent Interface

Provides an interface between Discord commands and the Dream.OS Cell Phone system.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from .messaging.cell_phone import CellPhone
from .messaging.enums import MessageMode
from .messaging.unified_message_system import (
    UnifiedMessageSystem,
    MessagePriority,
)

logger = logging.getLogger('discord_bot.agent_interface')

class AgentInterface:
    """Interface between Discord commands and Dream.OS Cell Phone system."""
    
    def __init__(self, runtime_dir: Optional[Path] = None):
        """Initialize the agent interface.
        
        Args:
            runtime_dir: Optional runtime directory for message storage
        """
        self.cell_phone = CellPhone()
        self.message_system = UnifiedMessageSystem(runtime_dir=runtime_dir)
        
    def send_command(self, command: str, agent_id: str, content: str, priority: int = 0) -> bool:
        """Send a command to an agent via the Cell Phone interface.
        
        Args:
            command: The command type (resume, verify, etc.)
            agent_id: The target agent ID
            content: The command content
            priority: Message priority (0-5)
            
        Returns:
            bool: True if command was sent successfully
        """
        try:
            # Map command to MessageMode
            mode_map = {
                'resume': MessageMode.RESUME,
                'verify': MessageMode.VERIFY,
                'repair': MessageMode.REPAIR,
                'backup': MessageMode.BACKUP,
                'restore': MessageMode.RESTORE,
                'sync': MessageMode.SYNC,
                'cleanup': MessageMode.CLEANUP,
                'task': MessageMode.TASK,
                'integrate': MessageMode.INTEGRATE,
                'normal': MessageMode.NORMAL
            }
            
            mode = mode_map.get(command.lower(), MessageMode.NORMAL)
            
            # Map priority to MessagePriority
            priority_map = {
                0: MessagePriority.LOW,
                1: MessagePriority.NORMAL,
                2: MessagePriority.HIGH,
                3: MessagePriority.CRITICAL
            }
            message_priority = priority_map.get(priority, MessagePriority.NORMAL)
            
            # Send message via Cell Phone
            success = self.cell_phone.send_message(
                from_agent="DISCORD",
                to_agent=agent_id,
                message=content,
                priority=priority,
                mode=mode
            )
            
            if success:
                # Also send via unified message system
                self.message_system.send(
                    to_agent=agent_id,
                    content=content,
                    from_agent="DISCORD",
                    metadata={"command": command},
                    mode=mode,
                    priority=message_priority,
                )
                logger.info(f"Command '{command}' sent to {agent_id}")
            else:
                logger.error(f"Failed to send command '{command}' to {agent_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
            
    def broadcast_command(self, command: str, content: str, priority: int = 0) -> Dict[str, bool]:
        """Broadcast a command to all agents.
        
        Args:
            command: The command type
            content: The command content
            priority: Message priority (0-5)
            
        Returns:
            Dict mapping agent IDs to success status
        """
        try:
            # Get list of all agents
            status = self.cell_phone.get_status()
            agents = [msg['to_agent'] for msg in status.get('messages', [])]
            agents = list(set(agents))  # Remove duplicates
            
            # Send command to each agent
            results = {}
            for agent_id in agents:
                results[agent_id] = self.send_command(command, agent_id, content, priority)
                
            return results
            
        except Exception as e:
            logger.error(f"Error broadcasting command: {e}")
            return {}
            
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of agent(s).
        
        Args:
            agent_id: Optional specific agent ID to check
            
        Returns:
            Dict containing agent status information
        """
        try:
            status = self.cell_phone.get_status()
            
            if agent_id:
                # Filter for specific agent
                agent_messages = [
                    msg for msg in status.get('messages', [])
                    if msg['to_agent'] == agent_id
                ]
                return {
                    'agent_id': agent_id,
                    'message_count': len(agent_messages),
                    'last_message': agent_messages[-1] if agent_messages else None
                }
            else:
                # Return status for all agents
                return status
                
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {}
            
    def clear_agent_messages(self, agent_id: Optional[str] = None) -> bool:
        """Clear messages for an agent or all agents.
        
        Args:
            agent_id: Optional specific agent ID to clear
            
        Returns:
            bool: True if messages were cleared successfully
        """
        try:
            self.cell_phone.clear_messages(agent_id)
            return True
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources."""
        try:
            asyncio.run(self.message_system.cleanup())
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Create singleton instance
_agent_interface = AgentInterface()

def send_command(command: str, agent_id: str, content: str, priority: int = 0) -> bool:
    """Send a command to an agent via the Cell Phone interface.
    
    Args:
        command: The command type (resume, verify, etc.)
        agent_id: The target agent ID
        content: The command content
        priority: Message priority (0-5)
        
    Returns:
        bool: True if command was sent successfully
    """
    return _agent_interface.send_command(command, agent_id, content, priority)

def broadcast_command(command: str, content: str, priority: int = 0) -> Dict[str, bool]:
    """Broadcast a command to all agents.
    
    Args:
        command: The command type
        content: The command content
        priority: Message priority (0-5)
        
    Returns:
        Dict mapping agent IDs to success status
    """
    return _agent_interface.broadcast_command(command, content, priority)

__all__ = [
    'AgentInterface',
    'send_command',
    'broadcast_command',
    'get_agent_status',
    'clear_agent_messages',
    'cleanup'
]
