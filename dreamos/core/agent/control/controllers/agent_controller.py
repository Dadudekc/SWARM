"""
Agent Controller Module

Handles control of individual agents, including lifecycle management and command routing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base_controller import BaseController
from dreamos.core.agent_control.agent_operations import AgentOperations

logger = logging.getLogger(__name__)

class AgentController(BaseController):
    """Controller for managing individual agents."""
    
    def __init__(self,
                 message_processor,
                 agent_status,
                 agent_ops: AgentOperations,
                 agent_id: str,
                 config: Optional[Dict[str, Any]] = None,
                 ui_automation: Optional['UIAutomation'] = None):
        """Initialize the agent controller.
        
        Args:
            message_processor: For handling message routing
            agent_status: For tracking agent state
            agent_ops: Agent operations interface
            agent_id: ID of the agent to control
            config: Optional configuration dictionary
            ui_automation: Optional UI automation instance
        """
        super().__init__(message_processor, agent_status, config)
        self.agent_ops = agent_ops
        self.agent_id = agent_id
        self._command_queue = asyncio.Queue()
        self._command_processor = None
        self.ui_automation = ui_automation
        
    async def initialize(self) -> bool:
        """Initialize the agent controller.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Verify agent exists
            if not await self.agent_ops.verify_agent(self.agent_id):
                logger.error(f"Agent {self.agent_id} not found")
                return False
                
            # Start command processor
            self._command_processor = asyncio.create_task(self._process_commands())
            
            self._initialized = True
            await self.update_status("initialized")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def start(self) -> bool:
        """Start the agent controller.
        
        Returns:
            bool: True if start successful
        """
        if not self._initialized:
            logger.error("Controller not initialized")
            return False
            
        try:
            # Start the agent
            if not await self.agent_ops.start_agent(self.agent_id):
                logger.error(f"Failed to start agent {self.agent_id}")
                return False
                
            self._running = True
            await self.update_status("running")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def stop(self) -> bool:
        """Stop the agent controller.
        
        Returns:
            bool: True if stop successful
        """
        if not self._running:
            return True
            
        try:
            # Stop the agent
            if not await self.agent_ops.stop_agent(self.agent_id):
                logger.error(f"Failed to stop agent {self.agent_id}")
                return False
                
            # Cancel command processor
            if self._command_processor:
                self._command_processor.cancel()
                self._command_processor = None
                
            self._running = False
            await self.update_status("stopped")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def resume(self) -> bool:
        """Resume the agent controller.
        
        Returns:
            bool: True if resume successful
        """
        if not self._initialized:
            logger.error("Controller not initialized")
            return False
            
        try:
            # Resume the agent
            if not await self.agent_ops.resume_agent(self.agent_id):
                logger.error(f"Failed to resume agent {self.agent_id}")
                return False
                
            # Restart command processor if needed
            if not self._command_processor:
                self._command_processor = asyncio.create_task(self._process_commands())
                
            self._running = True
            await self.update_status("running")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def send_command(self, command: str, priority: int = 0) -> None:
        """Send a command to the agent.
        
        Args:
            command: Command to send
            priority: Command priority (0 = normal)
        """
        await self._command_queue.put((command, priority))
        
    async def _process_commands(self) -> None:
        """Process commands from the queue."""
        try:
            while True:
                command, priority = await self._command_queue.get()
                try:
                    # Execute command
                    result = await self.agent_ops.execute_command(
                        self.agent_id,
                        command,
                        priority
                    )
                    
                    # Log result
                    if result:
                        logger.info(f"Command executed: {command}")
                    else:
                        logger.warning(f"Command failed: {command}")
                        
                except Exception as e:
                    logger.error(f"Error processing command: {e}")
                    
                finally:
                    self._command_queue.task_done()
                    
        except asyncio.CancelledError:
            logger.info("Command processor cancelled")
            raise
            
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status.
        
        Returns:
            Dict containing agent status information
        """
        return await self.agent_ops.get_agent_status(self.agent_id)
        
    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics.
        
        Returns:
            Dict containing agent metrics
        """
        return await self.agent_ops.get_agent_metrics(self.agent_id) 