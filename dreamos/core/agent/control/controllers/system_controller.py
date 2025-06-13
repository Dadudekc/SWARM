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
from dreamos.core.bridge.chatgpt.bridge import ChatGPTBridge
from dreamos.core.agent_control.agent_cellphone import AgentCellphone
from dreamos.core.bridge.handlers.outbox import BridgeOutboxHandler
from dreamos.core.shared.processors import MessageProcessor, ResponseProcessor, ProcessorFactory
from dreamos.core.shared.processors.mode import ProcessorMode

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
        
        # Bridge handlers
        self.bridge_handlers: Dict[str, BridgeOutboxHandler] = {}
        
        # State tracking
        self._monitor_task = None
        self._bridge_tasks: Dict[str, asyncio.Task] = {}
        
        # Bridge configuration
        self.bridge_config = config.get("bridge_config") if config else None
        if not self.bridge_config:
            self.bridge_config = {
                "model": "gpt-4",
                "max_retries": 2,
                "retry_backoff": 1.5,
                "timeout": 5.0
            }
        
        self.processor_factory = ProcessorFactory()
        self.response_processor = None
        
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
                
            # Initialize bridge
            if not self.bridge:
                self.bridge = ChatGPTBridge(self.bridge_config)
                
            # Create controllers for existing agents
            agent_ids = await self.agent_ops.list_agents()
            for agent_id in agent_ids:
                await self._create_agent_controller(agent_id)
                await self._start_bridge_handler(agent_id)
                
            # Create bridge outbox directory
            outbox_dir = Path(self.config.get("bridge_outbox_dir", "runtime/bridge_outbox"))
            outbox_dir.mkdir(parents=True, exist_ok=True)
            
            # Create processors
            self.message_processor = self.processor_factory.create('message', self.config)
            self.response_processor = self.processor_factory.create('response', {
                **self.config,
                'mode': ProcessorMode.CORE
            })
            
            # Start processors
            await self.message_processor.start()
            await self.response_processor.start()
            
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
                
            # Stop bridge handlers and wait for cleanup
            stop_tasks = []
            for handler in self.bridge_handlers.values():
                stop_tasks.append(handler.stop())
            if stop_tasks:
                await asyncio.gather(*stop_tasks, return_exceptions=True)
            self.bridge_handlers.clear()
            
            # Stop all agent controllers
            for controller in self.agent_controllers.values():
                await controller.stop()
                
            # Stop restarter and onboarder
            await self.restarter.stop()
            await self.onboarder.stop()
            
            # Stop processors
            if self.message_processor:
                await self.message_processor.stop()
            if self.response_processor:
                await self.response_processor.stop()
            
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
        """Start all agents and their bridge handlers."""
        try:
            # Get list of agents from agent_ops
            agent_ids = await self.agent_ops.list_agents()
            
            # Create tasks for all agent operations
            tasks = []
            for agent_id in agent_ids:
                async def start_agent(agent_id: str) -> None:
                    try:
                        # Check if agent needs onboarding
                        if await self._agent_needs_onboarding(agent_id):
                            if not await self.onboarder.onboard_agent(agent_id, "default"):
                                logger.error(f"Failed to onboard agent {agent_id}")
                                return
                                
                        # Check if agent needs recovery
                        elif await self._agent_needs_recovery(agent_id):
                            if not await self.restarter.handle_agent_error(agent_id):
                                logger.error(f"Failed to recover agent {agent_id}")
                                return
                                
                        # Start agent controller
                        if agent_id not in self.agent_controllers:
                            if not await self._create_agent_controller(agent_id):
                                logger.error(f"Failed to create controller for agent {agent_id}")
                                return
                                
                        controller = self.agent_controllers[agent_id]
                        if not await controller.start():
                            logger.error(f"Failed to start agent controller {agent_id}")
                            return
                            
                        # Start bridge handler
                        await self._start_bridge_handler(agent_id)
                    except Exception as e:
                        logger.error(f"Error starting agent {agent_id}: {e}")
                
                tasks.append(start_agent(agent_id))
            
            # Wait for all agent operations to complete
            await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Error starting agents: {e}")
            
    async def _start_bridge_handler(self, agent_id: str) -> bool:
        """Start bridge handler for agent.
        
        Args:
            agent_id: ID of agent to start handler for
            
        Returns:
            bool: True if handler started successfully
        """
        try:
            # Create agent directory
            agent_dir = Path(self.config.get("paths", {}).get("mailbox", "agent_tools/mailbox")) / f"agent-{agent_id}"
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize handler with config
            handler_config = {
                **self.bridge_config,
                "paths": {
                    "mailbox": str(agent_dir),
                    "archive": str(Path(self.config.get("paths", {}).get("archive", "archive"))),
                    "failed": str(Path(self.config.get("paths", {}).get("failed", "failed")))
                }
            }
            
            # Initialize handler
            handler = BridgeOutboxHandler(
                bridge=self.bridge,
                config=handler_config
            )
            
            # Start handler
            if not await handler.start():
                logger.error("Failed to start bridge handler for %s", agent_id)
                return False
            
            self.bridge_handlers[agent_id] = handler
            return True
            
        except Exception as e:
            logger.error("Error starting bridge handler for %s: %s", agent_id, str(e))
            return False
            
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
                            
                        # Check bridge handler
                        if agent_id in self._bridge_tasks:
                            task = self._bridge_tasks[agent_id]
                            if task.done():
                                logger.warning(f"Bridge handler for agent {agent_id} stopped")
                                await self._start_bridge_handler(agent_id)
                                
                    except Exception as e:
                        logger.error(f"Error monitoring agent {agent_id}: {e}")
                        
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except asyncio.CancelledError:
            logger.info("Agent monitoring cancelled")
            raise
            
    def get_bridge_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for a bridge handler.
        
        Args:
            agent_id: ID of the agent to get metrics for
            
        Returns:
            Dict[str, Any]: Bridge metrics
        """
        handler = self.bridge_handlers.get(agent_id)
        if not handler:
            return {
                "processed_messages": 0,
                "errors": {},
                "last_error": None
            }
        return handler.get_metrics()
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get the current system status.
        
        Returns:
            Dict[str, Any]: System status information
        """
        status = await super().get_system_status()
        
        # Add bridge metrics
        bridge_metrics = {}
        for agent_id, handler in self.bridge_handlers.items():
            bridge_metrics[agent_id] = handler.get_metrics()
        status["bridge_metrics"] = bridge_metrics
        
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
                config=self.config,
                ui_automation=self.config.get('ui_automation')
            )
            # Ensure controller is initialized before registering
            initialized = await controller.initialize()
            if not initialized:
                logger.error(f"Failed to initialize AgentController for {agent_id}")
                return False
            self.agent_controllers[agent_id] = controller
            return True
        except Exception as e:
            logger.error(f"Failed to create AgentController for {agent_id}: {e}")
            return False
        
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message.
        
        Args:
            message: Message to process
            
        Returns:
            Processed message
        """
        if not self.message_processor:
            raise RuntimeError("Message processor not initialized")
            
        return await self.message_processor.process(message)
        
    async def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            response: Response to process
            
        Returns:
            Processed response
        """
        if not self.response_processor:
            raise RuntimeError("Response processor not initialized")
            
        return await self.response_processor.process(response) 