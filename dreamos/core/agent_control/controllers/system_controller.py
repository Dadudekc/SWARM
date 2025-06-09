"""
System Controller Module

Orchestrates all agents in the system, providing high-level control and coordination.
Manages the complete agent lifecycle including onboarding, monitoring, recovery,
and bridge communication.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base_controller import BaseController
from .agent_controller import AgentController
from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus
from dreamos.core.agent_control.onboarding.agent_onboarder import AgentOnboarder
from dreamos.core.agent_control.agent_restarter import AgentRestarter
from dreamos.core.bridge.processors.bridge_response_loop_daemon import BridgeResponseLoopDaemon
from dreamos.core.bridge.chatgpt_bridge import ChatGPTBridge
from dreamos.core.agent_control.agent_cellphone import AgentCellphone

logger = logging.getLogger(__name__)

class SystemController(BaseController):
    """System-wide controller for managing agents and their interactions."""
    
    def __init__(self,
                 message_processor,
                 agent_status,
                 agent_ops: AgentOperations,
                 config: Optional[Dict[str, Any]] = None,
                 bridge: Optional[ChatGPTBridge] = None,
                 cellphone: Optional[AgentCellphone] = None):
        """Initialize the system controller.
        
        Args:
            message_processor: Message processing interface
            agent_status: Agent status tracker
            agent_ops: Agent operations interface
            config: Optional configuration dictionary
            bridge: Optional ChatGPT bridge instance (will create default if None)
            cellphone: Optional agent cellphone instance (will create default if None)
        """
        super().__init__(message_processor, agent_status, config)
        self.agent_ops = agent_ops
        self.agent_controllers: Dict[str, AgentController] = {}
        
        # Initialize components
        self.restarter = AgentRestarter(agent_ops, agent_status, config)
        self.cellphone = cellphone or AgentCellphone(config)
        self.onboarder = AgentOnboarder(agent_ops, agent_status, cellphone=self.cellphone, config=config)
        self.bridge = bridge or ChatGPTBridge(config)
        
        # Bridge loop daemons
        self.bridge_daemons: Dict[str, BridgeResponseLoopDaemon] = {}
        
        # State tracking
        self._monitor_task = None
        self._bridge_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize(self) -> bool:
        """Initialize the system controller.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize components
            if not await self.restarter.initialize():
                logger.error("Failed to initialize agent restarter")
                return False
                
            if not await self.onboarder.initialize():
                logger.error("Failed to initialize agent onboarder")
                return False
                
            # Create controllers for existing agents
            agent_ids = await self.agent_ops.list_agents()
            for agent_id in agent_ids:
                await self._create_agent_controller(agent_id)
                
            # Create bridge outbox directory
            outbox_dir = Path('runtime/bridge_outbox')
            outbox_dir.mkdir(parents=True, exist_ok=True)
            
            self._initialized = True
            await self.update_status("initialized")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def start(self) -> bool:
        """Start the system controller.
        
        Returns:
            bool: True if start successful
        """
        if not self._initialized:
            logger.error("Controller not initialized")
            return False
            
        try:
            # Start restarter and onboarder
            if not await self.restarter.start():
                logger.error("Failed to start agent restarter")
                return False
                
            if not await self.onboarder.start():
                logger.error("Failed to start agent onboarder")
                return False
                
            # Start all agents
            await self._start_all_agents()
            
            # Start monitoring
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            
            self._running = True
            await self.update_status("running")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def stop(self) -> bool:
        """Stop the system controller.
        
        Returns:
            bool: True if stop successful
        """
        if not self._running:
            return True
            
        try:
            # Stop monitoring
            if self._monitor_task:
                self._monitor_task.cancel()
                self._monitor_task = None
                
            # Stop bridge daemons
            for task in self._bridge_tasks.values():
                task.cancel()
            self._bridge_tasks.clear()
            self.bridge_daemons.clear()
            
            # Stop all agent controllers
            for controller in self.agent_controllers.values():
                await controller.stop()
                
            # Stop restarter and onboarder
            await self.restarter.stop()
            await self.onboarder.stop()
            
            self._running = False
            await self.update_status("stopped")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def resume(self) -> bool:
        """Resume the system controller after a pause.
        
        Returns:
            bool: True if resume successful
        """
        if self._running:
            return True
            
        try:
            # Resume restarter and onboarder
            if not await self.restarter.resume():
                logger.error("Failed to resume agent restarter")
                return False
                
            if not await self.onboarder.resume():
                logger.error("Failed to resume agent onboarder")
                return False
                
            # Resume all agents
            for controller in self.agent_controllers.values():
                if not await controller.resume():
                    logger.error(f"Failed to resume agent controller {controller}")
                    return False
                    
            # Restart monitoring
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            
            self._running = True
            await self.update_status("running")
            return True
            
        except Exception as e:
            await self.handle_error(e)
            return False
            
    async def _start_all_agents(self) -> None:
        """Start all agents and their bridge loops."""
        try:
            # Load agent configurations
            config_path = Path('config/agents.json')
            if not config_path.exists():
                logger.error("Agent configuration file not found")
                return
                
            with open(config_path, 'r') as f:
                agent_configs = json.load(f)
                
            for agent_config in agent_configs:
                agent_id = agent_config['id']
                role = agent_config['role']
                
                # Check if agent needs onboarding
                if await self._agent_needs_onboarding(agent_id):
                    if not await self.onboarder.onboard_agent(agent_id, role):
                        logger.error(f"Failed to onboard agent {agent_id}")
                        continue
                        
                # Check if agent needs recovery
                elif await self._agent_needs_recovery(agent_id):
                    if not await self.restarter.handle_agent_error(agent_id):
                        logger.error(f"Failed to recover agent {agent_id}")
                        continue
                        
                # Start agent controller
                if agent_id not in self.agent_controllers:
                    if not await self._create_agent_controller(agent_id):
                        logger.error(f"Failed to create controller for agent {agent_id}")
                        continue
                        
                controller = self.agent_controllers[agent_id]
                if not await controller.start():
                    logger.error(f"Failed to start agent controller {agent_id}")
                    continue
                    
                # Start bridge loop daemon
                await self._start_bridge_daemon(agent_id)
                
        except Exception as e:
            logger.error(f"Error starting agents: {e}")
            
    async def _start_bridge_daemon(self, agent_id: str) -> None:
        """Start a bridge loop daemon for an agent.
        
        Args:
            agent_id: ID of the agent to start daemon for
        """
        try:
            # Create daemon config
            config = {
                "paths": {
                    "base": str(Path("runtime/bridge_outbox")),
                    "outbox": str(Path("runtime/bridge_outbox") / agent_id),
                    "inbox": str(Path("runtime/bridge_inbox") / agent_id)
                },
                "bridge": {
                    "agent_id": agent_id,
                    "injector": self.cellphone.inject_prompt
                }
            }
            
            # Create daemon
            daemon = BridgeResponseLoopDaemon(config=config)
            
            # Store daemon
            self.bridge_daemons[agent_id] = daemon
            
            # Start daemon
            task = asyncio.create_task(daemon.start())
            self._bridge_tasks[agent_id] = task
            
            logger.info(f"Started bridge daemon for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error starting bridge daemon for agent {agent_id}: {e}")
            
    async def _agent_needs_onboarding(self, agent_id: str) -> bool:
        """Check if an agent needs onboarding.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if agent needs onboarding
        """
        try:
            status = await self.agent_status.get_agent_status(agent_id)
            return not status or status.get('status') != 'active'
        except Exception as e:
            logger.error(f"Error checking onboarding status for agent {agent_id}: {e}")
            return True
            
    async def _agent_needs_recovery(self, agent_id: str) -> bool:
        """Check if an agent needs recovery.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if agent needs recovery
        """
        try:
            status = await self.agent_status.get_agent_status(agent_id)
            return status and status.get('status') == 'error'
        except Exception as e:
            logger.error(f"Error checking recovery status for agent {agent_id}: {e}")
            return False
            
    async def _monitor_agents(self) -> None:
        """Monitor agent health and status."""
        try:
            while True:
                for agent_id, controller in self.agent_controllers.items():
                    try:
                        # Check agent status
                        status = await controller.get_agent_status()
                        if status.get("status") == "error":
                            logger.warning(f"Agent {agent_id} in error state")
                            await self.restarter.handle_agent_error(agent_id)
                            
                        # Check bridge daemon
                        if agent_id in self._bridge_tasks:
                            task = self._bridge_tasks[agent_id]
                            if task.done():
                                logger.warning(f"Bridge daemon for agent {agent_id} stopped")
                                await self._start_bridge_daemon(agent_id)
                                
                    except Exception as e:
                        logger.error(f"Error monitoring agent {agent_id}: {e}")
                        
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            logger.info("Agent monitoring cancelled")
            raise
            
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status.
        
        Returns:
            Dict containing system status information
        """
        status = {
            "running": self._running,
            "initialized": self._initialized,
            "agents": {}
        }
        
        for agent_id, controller in self.agent_controllers.items():
            agent_status = await controller.get_agent_status()
            if agent_id in self.bridge_daemons:
                agent_status['bridge_active'] = not self._bridge_tasks[agent_id].done()
            status["agents"][agent_id] = agent_status
            
        return status 

    async def _create_agent_controller(self, agent_id: str) -> bool:
        """Create and register an AgentController for the given agent_id."""
        try:
            if agent_id in self.agent_controllers:
                return True  # Already exists
            controller = AgentController(
                agent_id=agent_id,
                message_processor=self.message_processor,
                agent_ops=self.agent_ops,
                agent_status=self.agent_status,
                config=self.config
            )
            self.agent_controllers[agent_id] = controller
            return True
        except Exception as e:
            logger.error(f"Failed to create AgentController for {agent_id}: {e}")
            return False 