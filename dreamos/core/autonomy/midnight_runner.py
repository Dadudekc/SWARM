"""
Midnight Runner
--------------
Manages overnight operations and swarm maintenance.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from .autonomy_loop_runner import AutonomyLoopRunner
from ..logging.log_manager import LogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MidnightRunner:
    """Manages overnight operations and swarm maintenance."""
    
    def __init__(self, config_path: str = "config/midnight_config.json"):
        """Initialize the midnight runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.autonomy_loop = AutonomyLoopRunner()
        self.logger = LogManager()
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        
        # Initialize logging
        self.logger.info(
            platform="midnight_runner",
            status="initialized",
            message="Midnight runner initialized",
            tags=["init", "midnight"]
        )
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
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
                    platform="midnight_runner",
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
            failed_tests = await self.autonomy_loop.run_pytest_and_parse_failures()
            
            if failed_tests:
                self.logger.warning(
                    platform="midnight_runner",
                    status="warning",
                    message=f"Found {len(failed_tests)} failed tests",
                    tags=["test", "failure"]
                )
                
                # Let autonomy loop handle failures
                await asyncio.sleep(300)  # Wait 5 minutes for fixes
                
            # Stop autonomy loop
            await self.autonomy_loop.stop()
            
            self.logger.info(
                platform="midnight_runner",
                status="success",
                message="Completed midnight operations",
                tags=["midnight", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="midnight_runner",
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