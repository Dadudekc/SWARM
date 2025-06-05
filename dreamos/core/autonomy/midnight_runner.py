"""
Midnight Runner
--------------
Handles overnight operations:
1. Runs full test suite
2. Triggers inbox injection for broken tests
3. Restarts agent loop
4. Pushes commits
"""

import asyncio
import logging
import subprocess
import time
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Dict, Any, Optional

from ..logging.log_manager import LogManager
from .autonomy_loop_runner import AutonomyLoopRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MidnightRunner:
    """Manages overnight operations and swarm maintenance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the midnight runner.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        self.autonomy_loop = AutonomyLoopRunner(config)
        
        # Default configuration
        self.midnight_hour = self.config.get("midnight_hour", 0)  # 12 AM
        self.midnight_minute = self.config.get("midnight_minute", 0)
        self.check_interval = self.config.get("check_interval", 60)  # 1 minute
        self.max_retries = self.config.get("max_retries", 3)
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.last_run = None
        
        # Initialize logging
        self.logger.info(
            platform="midnight_runner",
            status="initialized",
            message="Midnight runner initialized",
            tags=["init", "midnight"]
        )
    
    async def start(self):
        """Start the midnight runner."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform="midnight_runner",
            status="started",
            message="Midnight runner started",
            tags=["start", "midnight"]
        )
    
    async def stop(self):
        """Stop the midnight runner."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform="midnight_runner",
            status="stopped",
            message="Midnight runner stopped",
            tags=["stop", "midnight"]
        )
    
    async def _run_overnight_tasks(self):
        """Run overnight maintenance tasks."""
        try:
            self.logger.info(
                platform="midnight_runner",
                status="starting",
                message="Starting overnight tasks",
                tags=["overnight", "start"]
            )
            
            # 1. Run full test suite
            await self._run_full_test_suite()
            
            # 2. Restart agent loop
            await self._restart_agent_loop()
            
            # 3. Push any pending commits
            await self._push_commits()
            
            self.last_run = datetime.now()
            
            self.logger.info(
                platform="midnight_runner",
                status="success",
                message="Completed overnight tasks",
                tags=["overnight", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="midnight_runner",
                status="error",
                message=f"Error in overnight tasks: {str(e)}",
                tags=["overnight", "error"]
            )
    
    async def _run_full_test_suite(self):
        """Run the full test suite."""
        try:
            # Run pytest with all tests
            process = await asyncio.create_subprocess_exec(
                "pytest",
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(
                    platform="midnight_runner",
                    status="test_failure",
                    message="Full test suite failed",
                    tags=["test", "failure"]
                )
                
                # Trigger autonomy loop to handle failures
                await self.autonomy_loop._run_tests()
            
        except Exception as e:
            self.logger.error(
                platform="midnight_runner",
                status="error",
                message=f"Error running test suite: {str(e)}",
                tags=["test", "error"]
            )
            raise
    
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
                platform="midnight_runner",
                status="success",
                message="Restarted agent loop",
                tags=["restart", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="midnight_runner",
                status="error",
                message=f"Error restarting agent loop: {str(e)}",
                tags=["restart", "error"]
            )
            raise
    
    async def _push_commits(self):
        """Push any pending commits."""
        try:
            # Check if there are commits to push
            process = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout.strip():
                # Push commits
                process = await asyncio.create_subprocess_exec(
                    "git",
                    "push",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if process.returncode == 0:
                    self.logger.info(
                        platform="midnight_runner",
                        status="success",
                        message="Pushed commits",
                        tags=["push", "success"]
                    )
                else:
                    self.logger.warning(
                        platform="midnight_runner",
                        status="warning",
                        message="Failed to push commits",
                        tags=["push", "warning"]
                    )
            
        except Exception as e:
            self.logger.error(
                platform="midnight_runner",
                status="error",
                message=f"Error pushing commits: {str(e)}",
                tags=["push", "error"]
            )
            raise
    
    def _should_run_tasks(self) -> bool:
        """Check if it's time to run overnight tasks.
        
        Returns:
            True if tasks should run
        """
        now = datetime.now()
        
        # Check if we've already run today
        if self.last_run and self.last_run.date() == now.date():
            return False
        
        # Check if it's midnight
        target_time = dt_time(self.midnight_hour, self.midnight_minute)
        return now.time() >= target_time
    
    async def _worker_loop(self):
        """Main worker loop for midnight runner."""
        while self.is_running:
            try:
                # Check if it's time to run tasks
                if self._should_run_tasks():
                    await self._run_overnight_tasks()
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    platform="midnight_runner",
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["worker", "error"]
                )
                await asyncio.sleep(5)  # Back off on error 