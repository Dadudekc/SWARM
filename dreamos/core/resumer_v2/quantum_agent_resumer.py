"""
Quantum Agent Resumer

Implements a quantum-aware agent resumption system with advanced state management
and error recovery capabilities.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import uuid

from .agent_state_manager import AgentStateManager, TaskState
from .atomic_file_manager import AtomicFileManager

logger = logging.getLogger(__name__)

class QuantumAgentResumer:
    """Quantum-aware agent resumption system."""
    
    def __init__(self, base_dir: str = "config/agent_comms"):
        """Initialize the quantum agent resumer.
        
        Args:
            base_dir: Base directory for agent communications
        """
        self.base_dir = Path(base_dir)
        self.state_manager = AgentStateManager(self.base_dir)
        
        # Health check and monitoring
        self.health_check_interval = 60  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics: Dict[str, Any] = {
            "cycle_count": 0,
            "errors": 0,
            "recoveries": 0,
            "last_health_check": None
        }
        
        # Initialize event handlers
        self._init_event_handlers()
        
    def _init_event_handlers(self):
        """Initialize event handlers."""
        asyncio.create_task(self.state_manager.register_event_handler(
            "state_update",
            self._handle_state_update
        ))
        asyncio.create_task(self.state_manager.register_event_handler(
            "task_added",
            self._handle_task_added
        ))
        asyncio.create_task(self.state_manager.register_event_handler(
            "task_updated",
            self._handle_task_updated
        ))
        asyncio.create_task(self.state_manager.register_event_handler(
            "debug_log",
            self._handle_debug_log
        ))
        
    async def start(self):
        """Start the quantum resumer system."""
        logger.info("Starting Quantum Agent Resumer")
        
        # Start health check loop
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Initialize state if needed
        if not await self.state_manager.validate_state():
            await self._initialize_state()
            
    async def stop(self):
        """Stop the quantum resumer system."""
        logger.info("Stopping Quantum Agent Resumer")
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
                
        await self.state_manager.cleanup()
        
    async def _health_check_loop(self):
        """Health check loop."""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retry
                
    async def _perform_health_check(self):
        """Perform health check."""
        try:
            # Check state validity
            state_valid = await self.state_manager.validate_state()
            if not state_valid:
                logger.warning("State validation failed, attempting recovery")
                await self._recover_state()
                
            # Check file integrity
            state_file = AtomicFileManager(self.base_dir / "agent_state.json")
            tasks_file = AtomicFileManager(self.base_dir / "tasks.json")
            
            state_valid = await state_file.validate_file()
            tasks_valid = await tasks_file.validate_file()
            
            if not (state_valid and tasks_valid):
                logger.error("File validation failed")
                await self._handle_validation_failure()
                
            # Update metrics
            self.metrics["last_health_check"] = datetime.now().isoformat()
            self.metrics["errors"] += 1 if not (state_valid and tasks_valid) else 0
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            self.metrics["errors"] += 1
            
    async def _recover_state(self):
        """Recover from invalid state."""
        try:
            # Attempt to restore from backup
            state_file = AtomicFileManager(self.base_dir / "agent_state.json")
            tasks_file = AtomicFileManager(self.base_dir / "tasks.json")
            
            state_recovered = await state_file._recover_from_backup()
            tasks_recovered = await tasks_file._recover_from_backup()
            
            if state_recovered and tasks_recovered:
                logger.info("State recovery successful")
                self.metrics["recoveries"] += 1
            else:
                logger.error("State recovery failed, initializing new state")
                await self._initialize_state()
                
        except Exception as e:
            logger.error(f"State recovery error: {str(e)}")
            await self._initialize_state()
            
    async def _initialize_state(self):
        """Initialize fresh state."""
        default_state = {
            "cycle_count": 0,
            "last_active": datetime.now().isoformat(),
            "mode": "normal",
            "test_debug": {
                "active": False,
                "start_time": None,
                "completed_cycles": 0
            }
        }
        
        await self.state_manager.update_state(default_state)
        logger.info("State initialized")
        
    async def activate_test_debug_mode(self):
        """Activate test debug mode."""
        state = await self.state_manager.get_state()
        if state is None:
            await self._initialize_state()
            state = await self.state_manager.get_state()
            
        state["mode"] = "test_debug"
        state["test_debug"] = {
            "active": True,
            "start_time": datetime.now().isoformat(),
            "completed_cycles": 0
        }
        
        await self.state_manager.update_state(state)
        await self.state_manager.log_debug("Test Debug Mode Activated")
        
    async def increment_cycle(self):
        """Increment cycle count."""
        state = await self.state_manager.get_state()
        if state is None:
            await self._initialize_state()
            state = await self.state_manager.get_state()
            
        state["cycle_count"] += 1
        state["last_active"] = datetime.now().isoformat()
        
        if state["mode"] == "test_debug":
            state["test_debug"]["completed_cycles"] += 1
            
        await self.state_manager.update_state(state)
        self.metrics["cycle_count"] = state["cycle_count"]
        
    async def add_test_fix_task(self, task_data: Dict[str, Any]):
        """Add a test fix task.
        
        Args:
            task_data: Task data
        """
        task = TaskState(
            id=str(uuid.uuid4()),
            type="TEST_FIX",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            data=task_data
        )
        
        await self.state_manager.add_task(task)
        
    async def add_blocker_task(self, task_data: Dict[str, Any]):
        """Add a blocker task.
        
        Args:
            task_data: Task data
        """
        task = TaskState(
            id=str(uuid.uuid4()),
            type="BLOCKER-TEST-DEBUG",
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            data=task_data
        )
        
        await self.state_manager.add_task(task)
        
    async def get_test_debug_status(self) -> Dict[str, Any]:
        """Get test debug status.
        
        Returns:
            Dict: Test debug status
        """
        state = await self.state_manager.get_state()
        if state is None:
            return {
                "mode": "unknown",
                "cycle_count": 0,
                "test_debug": {
                    "active": False,
                    "start_time": None,
                    "completed_cycles": 0
                }
            }
            
        return {
            "mode": state["mode"],
            "cycle_count": state["cycle_count"],
            "test_debug": state["test_debug"]
        }
        
    async def _handle_state_update(self, state: Dict[str, Any]):
        """Handle state update event.
        
        Args:
            state: Updated state
        """
        logger.debug(f"State updated: {state}")
        
    async def _handle_task_added(self, task: TaskState):
        """Handle task added event.
        
        Args:
            task: Added task
        """
        logger.debug(f"Task added: {task}")
        
    async def _handle_task_updated(self, task: Dict[str, Any]):
        """Handle task updated event.
        
        Args:
            task: Updated task
        """
        logger.debug(f"Task updated: {task}")
        
    async def _handle_debug_log(self, log_entry: Dict[str, Any]):
        """Handle debug log event.
        
        Args:
            log_entry: Log entry
        """
        logger.debug(f"Debug log: {log_entry}")
        
    async def _handle_validation_failure(self):
        """Handle validation failure."""
        logger.error("Validation failure detected")
        await self._recover_state() 