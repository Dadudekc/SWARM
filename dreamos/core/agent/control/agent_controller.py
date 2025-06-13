"""
Agent Controller Module

This module provides comprehensive agent control functionality for Dream.OS.
It handles agent lifecycle management, command execution, and state control.
"""

from typing import Dict, List, Optional, Any, Callable
import logging
import asyncio
from datetime import datetime

from ..state import AgentState
from ..lifecycle import AgentManager
from .agent_status import AgentStatus, AgentStatusInfo, AgentStatusTracker
from .agent_operations import AgentOperations

logger = logging.getLogger(__name__)

class AgentController:
    """Agent control and lifecycle management."""
    
    def __init__(self, agent_manager: AgentManager):
        """Initialize agent controller.
        
        Args:
            agent_manager: The agent manager instance
        """
        self.agent_manager = agent_manager
        self.status_tracker = AgentStatusTracker(agent_manager)
        self.operations = AgentOperations(agent_manager)
        self._command_handlers: Dict[str, Callable] = {}
        self._setup_command_handlers()
        
    def _setup_command_handlers(self) -> None:
        """Set up command handlers."""
        self._command_handlers = {
            'start': self._handle_start,
            'stop': self._handle_stop,
            'restart': self._handle_restart,
            'status': self._handle_status,
            'health': self._handle_health,
            'command': self._handle_command
        }
        
    async def execute_command(self, agent_id: str, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command on an agent.
        
        Args:
            agent_id: The ID of the agent
            command: The command to execute
            args: Optional command arguments
            
        Returns:
            Dict[str, Any]: Command execution result
        """
        try:
            if command not in self._command_handlers:
                raise ValueError(f"Unknown command: {command}")
                
            handler = self._command_handlers[command]
            result = await handler(agent_id, args or {})
            
            logger.info(f"Executed command {command} on agent {agent_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute command {command} on agent {agent_id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def _handle_start(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Start result
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
                
            await self.operations.start_agent(agent)
            self.status_tracker.update_status(agent_id, AgentStatus.IDLE)
            
            return {
                'status': 'success',
                'message': f'Started agent {agent_id}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.status_tracker.update_status(agent_id, AgentStatus.ERROR, {'error': str(e)})
            raise
            
    async def _handle_stop(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Stop result
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
                
            await self.operations.stop_agent(agent)
            self.status_tracker.update_status(agent_id, AgentStatus.SHUTDOWN)
            
            return {
                'status': 'success',
                'message': f'Stopped agent {agent_id}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.status_tracker.update_status(agent_id, AgentStatus.ERROR, {'error': str(e)})
            raise
            
    async def _handle_restart(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle restart command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Restart result
        """
        try:
            await self._handle_stop(agent_id, args)
            await asyncio.sleep(1)  # Brief pause between stop and start
            return await self._handle_start(agent_id, args)
            
        except Exception as e:
            self.status_tracker.update_status(agent_id, AgentStatus.ERROR, {'error': str(e)})
            raise
            
    async def _handle_status(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Status result
        """
        try:
            status_info = self.status_tracker.get_current_status(agent_id)
            if not status_info:
                raise ValueError(f"No status found for agent {agent_id}")
                
            return {
                'status': 'success',
                'data': status_info.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for agent {agent_id}: {str(e)}")
            raise
            
    async def _handle_health(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Health check result
        """
        try:
            health_info = self.status_tracker.run_health_check(agent_id)
            
            return {
                'status': 'success',
                'data': health_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to run health check for agent {agent_id}: {str(e)}")
            raise
            
    async def _handle_command(self, agent_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom command.
        
        Args:
            agent_id: The ID of the agent
            args: Command arguments
            
        Returns:
            Dict[str, Any]: Command result
        """
        try:
            command = args.get('command')
            if not command:
                raise ValueError("No command specified")
                
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
                
            self.status_tracker.update_status(agent_id, AgentStatus.BUSY)
            
            result = await self.operations.execute_command(agent, command, args)
            
            self.status_tracker.update_status(agent_id, AgentStatus.IDLE)
            
            return {
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.status_tracker.update_status(agent_id, AgentStatus.ERROR, {'error': str(e)})
            raise 
