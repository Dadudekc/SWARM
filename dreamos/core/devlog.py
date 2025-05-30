"""
DevLog Manager

Manages development logs for agents and system components.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger('devlog')

class DevLogManager:
    """Manages development logs for agents and system components."""
    
    def __init__(self):
        """Initialize DevLogManager."""
        self.logs: Dict[str, Any] = {}
        
    def log_event(self, agent_id: str, event: str, data: Optional[Dict] = None):
        """Log an event for an agent.
        
        Args:
            agent_id: ID of the agent
            event: Event type
            data: Optional event data
        """
        logger.debug(f"Logging event for {agent_id}: {event}")
        if agent_id not in self.logs:
            self.logs[agent_id] = []
        self.logs[agent_id].append({"event": event, "data": data})
        
    def get_logs(self, agent_id: str) -> list:
        """Get logs for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of log entries
        """
        return self.logs.get(agent_id, [])
        
    def clear_logs(self, agent_id: str):
        """Clear logs for an agent.
        
        Args:
            agent_id: ID of the agent
        """
        if agent_id in self.logs:
            self.logs[agent_id] = [] 