"""
Quantum Agent Resumer

Manages agent state persistence and resumption.
"""

import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import uuid
from dreamos.core.messaging.enums import TaskStatus
from dreamos.core.resumer_v2.agent_state_manager import AgentStateManager

from .atomic_file_manager import AtomicFileManager

logger = logging.getLogger(__name__)

class QuantumAgentResumer:
    """Manages agent state persistence and resumption."""
    
    def __init__(self, base_dir: str, agent_id: str = "default"):
        """Initialize the resumer.
        
        Args:
            base_dir: Base directory for state files
            agent_id: Agent identifier
        """
        self.base_dir = Path(base_dir)
        self.agent_id = agent_id
        self.state_manager = AgentStateManager(str(self.base_dir), agent_id)
        self.file_manager = AtomicFileManager(str(self.base_dir))
        self._running = False
        self._event_handlers_initialized = False
        
        # Health check and monitoring
        self.health_check_interval = 60  # seconds
        self.health_check_task = None
        self.metrics: Dict[str, Any] = {
            "cycle_count": 0,
            "errors": 0,
            "recoveries": 0,
            "last_health_check": None
        }
        
    async def _init_event_handlers(self):
        """Initialize event handlers."""
        await self.state_manager.register_handler("state_update", self._handle_state_update)
        await self.state_manager.register_handler("task_add", self._handle_task_add)
        await self.state_manager.register_handler("task_update", self._handle_task_update)
        self._event_handlers_initialized = True
        
    async def _handle_state_update(self, state: Dict[str, Any]):
        """Handle state update events."""
        logger.debug(f"State updated: {state}")
        
    async def _handle_task_add(self, task: Dict[str, Any]):
        """Handle task add events."""
        logger.debug(f"Task added: {task}")
        
    async def _handle_task_update(self, task: Dict[str, Any]):
        """Handle task update events."""
        logger.debug(f"Task updated: {task}")
        
    async def start(self):
        """Start the resumer."""
        if self._running:
            return
            
        logger.info("Starting Quantum Agent Resumer")
        self._running = True
        
        # Initialize event handlers
        if not self._event_handlers_initialized:
            await self._init_event_handlers()
        
        # Initialize state
        state = await self.state_manager.get_state()
        if state["status"] == "idle":
            await self.state_manager.update_state({"status": "running"})
            
        # Start health check loop
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Initialize state if needed
        state = await self.state_manager.get_state()
        if state is None:
            await self._initialize_state()
            state = await self.state_manager.get_state()
            if state is None:
                raise RuntimeError("Failed to initialize state")
            
    async def stop(self):
        """Stop the resumer."""
        if not self._running:
            return
            
        logger.info("Stopping Quantum Agent Resumer")
        self._running = False
        
        # Update state
        await self.state_manager.update_state({"status": "idle"})
        
        # Clean up files
        await self._cleanup_files()
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
        
    async def _cleanup_files(self):
        """Clean up temporary files."""
        try:
            # Close any open file handles
            self.state_manager = None
            self.file_manager = None
            
            # Give Windows time to release file handles
            await asyncio.sleep(0.1)
            
            # Try to remove files with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Remove individual files first
                    for file in self.base_dir.glob("*"):
                        try:
                            file.unlink()
                        except Exception as e:
                            logger.warning(f"Error removing file {file}: {e}")
                            
                    # Then remove directory
                    if self.base_dir.exists():
                        shutil.rmtree(self.base_dir)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} cleaning up files: {e}")
                        await asyncio.sleep(0.1)
                    else:
                        logger.error(f"Error cleaning up base directory: {e}")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
        
    async def _health_check_loop(self):
        """Periodic health check loop."""
        while True:
            try:
                state = await self.state_manager.get_state()
                if not self.state_manager.validate_state(state):
                    logger.error("Invalid state detected during health check")
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
                
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
        
    async def increment_cycle(self) -> bool:
        """Increment cycle count."""
        state = await self.state_manager.get_state()
        state["cycle_count"] = state.get("cycle_count", 0) + 1
        state["last_updated"] = datetime.now().isoformat()
        return await self.state_manager._write_state_file_async(state)
        
    async def activate_test_debug_mode(self) -> bool:
        """Activate test debug mode."""
        state = await self.state_manager.get_state()
        state["debug_mode"] = True
        state["last_updated"] = datetime.now().isoformat()
        return await self.state_manager._write_state_file_async(state)
        
    async def add_test_fix_task(self, task_data: Dict[str, Any]):
        """Add a test fix task.
        
        Args:
            task_data: Task data
        """
        task = {
            "id": str(uuid.uuid4()),
            "type": "TEST_FIX",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": task_data,
        }
        
        await self.state_manager.add_task(task)
        return task
        
    async def add_blocker_task(self, task_data: Dict[str, Any]):
        """Add a blocker task.
        
        Args:
            task_data: Task data
        """
        task = {
            "id": str(uuid.uuid4()),
            "type": "BLOCKER-TEST-DEBUG",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": task_data,
        }
        
        await self.state_manager.add_task(task)
        return task
        
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
        
    async def _handle_validation_failure(self):
        """Handle validation failure."""
        logger.error("Validation failure detected")
        await self._recover_state()
        
    async def cleanup(self):
        """Cleanup resources."""
        await self.stop()
        await self._cleanup_files()
