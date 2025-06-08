"""
Midnight Runner
--------------
Manages overnight operations and swarm maintenance.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from .base.runner_core import RunnerCore
from .autonomy_loop_runner import AutonomyLoopRunner
from .handlers.bridge_outbox_handler import BridgeOutboxHandler
from .codex_patch_tracker import CodexPatchTracker

logger = logging.getLogger(__name__)

class MidnightRunner(RunnerCore[str]):
    """Manages overnight operations and swarm maintenance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the midnight runner.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config, platform="midnight_runner")
        
        # Initialize components
        self.bridge_handler = BridgeOutboxHandler()
        self.patch_tracker = CodexPatchTracker()
        
        # Maintenance-specific configuration
        self.maintenance_tasks = self.config.get("maintenance_tasks", [])
        
        self.autonomy_loop = AutonomyLoopRunner()
    
    async def _worker_loop(self):
        """Main worker loop for overnight operations."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's midnight
                if current_time.hour == 0 and current_time.minute == 0:
                    await self._run_midnight_operations()
                
                # Sleep until next minute
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(
                    platform=self.platform,
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["error", "worker_loop"]
                )
                await asyncio.sleep(60)  # Sleep on error
    
    async def _run_midnight_operations(self):
        """Run overnight maintenance operations."""
        try:
            # Start autonomy loop
            await self.autonomy_loop.start()
            
            # Run full test suite
            test_results = await self.run_tests()
            failed_tests = self.parse_test_failures(test_results["stdout"])
            
            if failed_tests:
                self.logger.warning(
                    platform=self.platform,
                    status="warning",
                    message=f"Found {len(failed_tests)} failed tests",
                    tags=["test", "failure"]
                )
                
                # Let autonomy loop handle failures
                await asyncio.sleep(300)  # Wait 5 minutes for fixes
                
            # Stop autonomy loop
            await self.autonomy_loop.stop()
            
            self.logger.info(
                platform=self.platform,
                status="success",
                message="Completed midnight operations",
                tags=["midnight", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform=self.platform,
                status="error",
                message=f"Error in midnight operations: {str(e)}",
                tags=["midnight", "error"]
            )
            # Ensure autonomy loop is stopped
            await self.autonomy_loop.stop()
    
    async def _restart_agent_loop(self):
        """Restart the agent loop."""
        try:
            # Stop current loop
            await self.autonomy_loop.stop()
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Start fresh loop
            await self.autonomy_loop.start()
            
            self.logger.info(
                platform=self.platform,
                status="success",
                message="Restarted agent loop",
                tags=["restart", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform=self.platform,
                status="error",
                message=f"Error restarting agent loop: {str(e)}",
                tags=["restart", "error"]
            )
            raise 

    async def _run_iteration(self):
        """Run a single iteration of maintenance tasks."""
        # Get maintenance tasks
        tasks = await self._get_maintenance_tasks()
        
        for task in tasks:
            if task not in self.in_progress_items:
                await self.item_queue.put(task)
                self.in_progress_items.add(task)
    
    async def _handle_result(self, result: Any):
        """Handle a maintenance task result.
        
        Args:
            result: Task result to handle
        """
        if isinstance(result, dict):
            task_name = result.get("task_name")
            success = result.get("success", False)
            
            if task_name in self.in_progress_items:
                self.in_progress_items.remove(task_name)
                
                if success:
                    self.passed_items.add(task_name)
                    if task_name in self.failed_items:
                        self.failed_items.remove(task_name)
                else:
                    self.failed_items.add(task_name)
                    if task_name in self.passed_items:
                        self.passed_items.remove(task_name)
    
    async def _get_maintenance_tasks(self) -> List[str]:
        """Get list of maintenance tasks to run.
        
        Returns:
            List of maintenance task names
        """
        return self.maintenance_tasks 
