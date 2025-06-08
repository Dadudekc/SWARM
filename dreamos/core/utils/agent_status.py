"""
Agent Status Module

Manages agent status tracking and updates.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def _ensure_status_file(agent_id):
    """Ensure status file exists for agent."""
    # TODO: Implement actual status file creation logic
    pass

class AgentStatus:
    """Manages agent status tracking."""
    
    def __init__(self, status_file: str):
        """Initialize the status manager.
        
        Args:
            status_file: Path to status file
        """
        self.status_file = status_file
        self._ensure_status_file()
        
    def _ensure_status_file(self):
        """Ensure status file exists."""
        if not os.path.exists(self.status_file):
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            with open(self.status_file, 'w') as f:
                json.dump({}, f)
                
    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get status for an agent.
        
        Args:
            agent_id: Agent ID to get status for
            
        Returns:
            Agent status dictionary
        """
        try:
            with open(self.status_file, 'r') as f:
                statuses = json.load(f)
            return statuses.get(agent_id, {})
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {}
            
    async def get_all_agent_statuses(self) -> Dict:
        """Get status for all agents.
        
        Returns:
            Dictionary of all agent statuses
        """
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting all agent statuses: {e}")
            return {}
            
    async def update_agent_status(self, 
                                agent_id: str,
                                status: str,
                                extra_data: Optional[Dict] = None) -> bool:
        """Update status for an agent.
        
        Args:
            agent_id: Agent ID to update
            status: New status
            extra_data: Additional status data
            
        Returns:
            True if update successful
        """
        try:
            # Read current statuses
            with open(self.status_file, 'r') as f:
                statuses = json.load(f)
                
            # Update status
            statuses[agent_id] = {
                "status": status,
                "last_heartbeat": datetime.now().isoformat(),
                **(extra_data or {})
            }
            
            # Write back
            with open(self.status_file, 'w') as f:
                json.dump(statuses, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
            return False 