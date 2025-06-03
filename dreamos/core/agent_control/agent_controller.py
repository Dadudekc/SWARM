"""
Agent Controller

Manages agent operations and UI interactions.
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from .ui_automation import UIAutomation
from .periodic_restart import AgentResumeManager

logger = logging.getLogger('agent_controller')

class AgentController(QObject):
    """Controls agent operations and UI interactions"""
    
    agent_changed = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, ui_automation: UIAutomation):
        """Initialize agent controller
        
        Args:
            ui_automation: UI automation instance
        """
        super().__init__()
        self.ui_automation = ui_automation
        self.current_agent: Optional[str] = None
        self.resume_manager = AgentResumeManager(ui_automation)
        
        # Connect signals
        self.agent_changed.connect(self._handle_agent_change)
        self.status_updated.connect(self.ui_automation.update_status)
        
    def _handle_agent_change(self, agent_id: str):
        """Handle agent change
        
        Args:
            agent_id: ID of the new agent
        """
        logger.debug(f"Agent changed to: {agent_id}")
        self.current_agent = agent_id
        self.status_updated.emit(f"Switched to agent: {agent_id}")
        
    def resume_agent(self, agent_id: str):
        """Resume agent operations
        
        Args:
            agent_id: ID of agent to resume
        """
        try:
            logger.debug(f"Resuming agent: {agent_id}")
            self.current_agent = agent_id
            self.status_updated.emit(f"Resuming agent: {agent_id}")
            
            # Start resume checks for all agents
            self.resume_manager.start_resume_checks(agent_id)
            logger.info(f"Started resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            self.ui_automation.handle_error(f"Error resuming {agent_id}: {str(e)}")
            
    def verify_agent(self, agent_id: str):
        """Verify agent status
        
        Args:
            agent_id: ID of agent to verify
        """
        try:
            logger.debug(f"Verifying agent: {agent_id}")
            self.status_updated.emit(f"Verifying agent: {agent_id}")
            
            # Ensure resume checks are running
            if agent_id not in self.resume_manager.resume_timers:
                self.resume_manager.start_resume_checks(agent_id)
                logger.info(f"Started resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error verifying agent: {e}")
            self.ui_automation.handle_error(f"Error verifying {agent_id}: {str(e)}")
            
    def cleanup_agent(self, agent_id: str):
        """Clean up agent resources
        
        Args:
            agent_id: ID of agent to clean up
        """
        try:
            logger.debug(f"Cleaning up agent: {agent_id}")
            self.status_updated.emit(f"Cleaning up agent: {agent_id}")
            
            # Stop resume checks
            self.resume_manager.stop_resume_checks(agent_id)
            logger.info(f"Stopped resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up agent: {e}")
            self.ui_automation.handle_error(f"Error cleaning up {agent_id}: {str(e)}")
            
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed status for an agent.
        
        Args:
            agent_id: ID of agent to get status for
            
        Returns:
            Dict containing agent status information
        """
        status = {
            "agent_id": agent_id,
            "is_current": agent_id == self.current_agent,
            "last_resume": None
        }
        
        if agent_id == "Agent-3":
            status.update({
                "periodic_restart_enabled": agent_id in self.restart_manager.restart_timers,
                "last_restart": self.restart_manager.last_restart.get(agent_id)
            })
            
        return status 