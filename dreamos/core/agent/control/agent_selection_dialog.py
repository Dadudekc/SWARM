"""
Agent Selection Dialog Module

This module provides a UI dialog for selecting agents in Dream.OS.
It handles agent selection, filtering, and status display.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..state import AgentState
from ..lifecycle import AgentManager
from .agent_status import AgentStatus

logger = logging.getLogger(__name__)

class AgentSelectionDialog:
    """UI dialog for agent selection."""
    
    def __init__(self, agent_manager: AgentManager, agent_status: AgentStatus):
        """Initialize agent selection dialog.
        
        Args:
            agent_manager: The agent manager instance
            agent_status: The agent status tracker
        """
        self.agent_manager = agent_manager
        self.agent_status = agent_status
        self._selected_agent: Optional[str] = None
        self._filter_criteria: Dict[str, Any] = {}
        
    def show(self) -> Optional[str]:
        """Show the agent selection dialog.
        
        Returns:
            Optional[str]: Selected agent ID or None if cancelled
        """
        try:
            # Get available agents
            agents = self._get_available_agents()
            
            if not agents:
                logger.warning("No agents available for selection")
                return None
                
            # Apply filters
            filtered_agents = self._apply_filters(agents)
            
            if not filtered_agents:
                logger.warning("No agents match current filters")
                return None
                
            # Show dialog and get selection
            self._selected_agent = self._show_dialog(filtered_agents)
            
            if self._selected_agent:
                logger.info(f"Selected agent: {self._selected_agent}")
                
            return self._selected_agent
            
        except Exception as e:
            logger.error(f"Failed to show agent selection dialog: {str(e)}")
            return None
            
    def set_filter(self, criteria: Dict[str, Any]) -> None:
        """Set filter criteria for agent selection.
        
        Args:
            criteria: Filter criteria dictionary
        """
        self._filter_criteria = criteria
        logger.info(f"Updated filter criteria: {criteria}")
        
    def clear_filter(self) -> None:
        """Clear all filter criteria."""
        self._filter_criteria = {}
        logger.info("Cleared filter criteria")
        
    def _get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their details.
        
        Returns:
            List[Dict[str, Any]]: List of agent details
        """
        agents = []
        
        for agent_id in self.agent_manager.get_agent_ids():
            status = self.agent_status.get_current_status(agent_id)
            if status:
                agents.append({
                    'id': agent_id,
                    'status': status['status'],
                    'last_updated': status['timestamp'],
                    'details': status['details']
                })
                
        return agents
        
    def _apply_filters(self, agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters to agent list.
        
        Args:
            agents: List of agent details
            
        Returns:
            List[Dict[str, Any]]: Filtered list of agent details
        """
        if not self._filter_criteria:
            return agents
            
        filtered = []
        
        for agent in agents:
            matches = True
            
            for key, value in self._filter_criteria.items():
                if key not in agent or agent[key] != value:
                    matches = False
                    break
                    
            if matches:
                filtered.append(agent)
                
        return filtered
        
    def _show_dialog(self, agents: List[Dict[str, Any]]) -> Optional[str]:
        """Show the selection dialog UI.
        
        Args:
            agents: List of agent details to display
            
        Returns:
            Optional[str]: Selected agent ID or None if cancelled
        """
        # TODO: Implement actual UI dialog
        # For now, just return the first agent
        return agents[0]['id'] if agents else None 
