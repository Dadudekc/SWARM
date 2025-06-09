"""
Discord Bot Agent Interface

Provides an interface between Discord commands and the Dream.OS Cell Phone system.
"""

import logging
from dreamos.core.agent_interface import (
    AgentInterface,
    send_command,
    broadcast_command,
    get_agent_status,
    clear_agent_messages,
    cleanup
)
from typing import Dict, List, Optional, Any

logger = logging.getLogger('discord_bot.agent_interface')

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

def get_agent_status(agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Get status of agent(s).
    
    Args:
        agent_id: Optional specific agent ID to check
        
    Returns:
        Dict containing agent status information
    """
    return _agent_interface.get_agent_status(agent_id)

def clear_agent_messages(agent_id: Optional[str] = None) -> bool:
    """Clear messages for an agent or all agents.
    
    Args:
        agent_id: Optional specific agent ID to clear
        
    Returns:
        bool: True if messages were cleared successfully
    """
    return _agent_interface.clear_agent_messages(agent_id)

def cleanup():
    """Clean up resources."""
    _agent_interface.cleanup() 
