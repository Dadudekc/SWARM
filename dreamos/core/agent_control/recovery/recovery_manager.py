"""
Recovery Management Module

Handles agent recovery operations including restarting conversations,
managing recovery state, and coordinating recovery actions.
"""

import asyncio
import logging
from typing import Dict, Optional, Set

from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus
from dreamos.core.agent_control.recovery.window_manager import WindowManager
from dreamos.core.shared.coordinate_manager import CoordinateManager
from dreamos.core.agent_control.recovery.heartbeat_monitor import HeartbeatMonitor

logger = logging.getLogger(__name__)

class RecoveryManager:
    """Manages agent recovery operations."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 config: Optional[Dict] = None):
        """Initialize the recovery manager."""
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.config = config or {}
        
        # Initialize components
        self.window_manager = WindowManager()
        self.coordinate_manager = CoordinateManager(recovery_mode=True)
        self.heartbeat_monitor = HeartbeatMonitor(agent_ops, agent_status, config)
        
        # Recovery state
        self._recovery_in_progress: Set[str] = set()
        self._recovery_queue: asyncio.Queue[str] = asyncio.Queue()
        self._recovery_task = None
        
    async def start(self) -> bool:
        """Start recovery management.
        
        Returns:
            bool: True if started successfully
        """
        try:
            # Start heartbeat monitoring
            if not await self.heartbeat_monitor.start():
                return False
                
            # Start recovery processing
            self._recovery_task = asyncio.create_task(self._process_recovery_queue())
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recovery manager: {e}")
            return False
            
    async def stop(self) -> bool:
        """Stop recovery management.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            # Stop heartbeat monitoring
            if not await self.heartbeat_monitor.stop():
                return False
                
            # Stop recovery processing
            if self._recovery_task:
                self._recovery_task.cancel()
                try:
                    await self._recovery_task
                except asyncio.CancelledError:
                    pass
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recovery manager: {e}")
            return False
            
    async def handle_agent_error(self, agent_id: str, error: Exception) -> None:
        """Handle an agent error.
        
        Args:
            agent_id: ID of the agent that encountered an error
            error: The error that occurred
        """
        try:
            # Log error
            logger.error(f"Agent {agent_id} encountered error: {error}")
            
            # Add to recovery queue if not already in progress
            if agent_id not in self._recovery_in_progress:
                await self._recovery_queue.put(agent_id)
                
        except Exception as e:
            logger.error(f"Error handling agent error: {e}")
            
    async def _process_recovery_queue(self) -> None:
        """Process the recovery queue."""
        while True:
            try:
                # Get next agent to recover
                agent_id = await self._recovery_queue.get()
                
                # Skip if already in progress
                if agent_id in self._recovery_in_progress:
                    continue
                    
                # Mark as in progress
                self._recovery_in_progress.add(agent_id)
                
                try:
                    # Attempt recovery
                    await self._recover_agent(agent_id)
                finally:
                    # Remove from in progress
                    self._recovery_in_progress.remove(agent_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing recovery queue: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
    async def _recover_agent(self, agent_id: str) -> None:
        """Recover a specific agent.
        
        Args:
            agent_id: ID of the agent to recover
        """
        try:
            # Get agent window
            window = self.window_manager.find_cursor_window(agent_id)
            if not window:
                logger.error(f"Could not find window for agent {agent_id}")
                return
                
            # Check if window is idle
            if not self.window_manager.check_window_idle(agent_id):
                logger.warning(f"Window not idle for agent {agent_id}")
                return
                
            # Get coordinates
            if not self.coordinate_manager.has_coordinates(agent_id):
                logger.error(f"No coordinates found for agent {agent_id}")
                return
                
            # Activate window
            if not self.window_manager.activate_window(window):
                logger.error(f"Could not activate window for agent {agent_id}")
                return
                
            # Restart conversation
            await self._restart_conversation(agent_id)
            
            # Update status
            await self.agent_status.update_agent_status(agent_id, "recovered")
            
        except Exception as e:
            logger.error(f"Error recovering agent {agent_id}: {e}")
            
    async def _restart_conversation(self, agent_id: str) -> None:
        """Restart a conversation for an agent.
        
        Args:
            agent_id: ID of the agent to restart
        """
        try:
            # Get coordinates
            coords = self.coordinate_manager.get_coordinates(agent_id)
            
            # Click input field
            await self.agent_ops.click_position(coords["input_field"])
            
            # Send restart command
            await self.agent_ops.send_keys("^a")  # Select all
            await self.agent_ops.send_keys("{BACKSPACE}")  # Clear
            await self.agent_ops.send_keys("/restart")  # Restart command
            await self.agent_ops.send_keys("{ENTER}")  # Execute
            
            # Wait for restart
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error restarting conversation for agent {agent_id}: {e}")
            raise
            
    def get_recovery_status(self) -> Dict[str, bool]:
        """Get recovery status for all agents.
        
        Returns:
            Dict[str, bool]: Map of agent IDs to recovery status
        """
        return {
            agent_id: agent_id in self._recovery_in_progress
            for agent_id in self.heartbeat_monitor.get_failed_agents()
        } 