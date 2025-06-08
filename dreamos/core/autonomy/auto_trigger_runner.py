"""
Auto Trigger Runner
-----------------
Manages automatic test failure handling and fix loops.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List

from .base.runner_core import RunnerCore
from .handlers.bridge_outbox_handler import BridgeOutboxHandler
from .codex_patch_tracker import CodexPatchTracker

logger = logging.getLogger(__name__)

class AutoTriggerRunner(RunnerCore[str]):
    """Manages automatic test failure handling and fix loops."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the auto trigger runner.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config, platform="auto_trigger")
        
        # Initialize components
        self.bridge_handler = BridgeOutboxHandler()
        self.patch_tracker = CodexPatchTracker()
        
        # Auto trigger specific settings
        self.trigger_interval = self.config.get("trigger_interval", 300)  # 5 minutes
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 60)  # 1 minute
        
        # State tracking
        self.current_retries = 0
        self.last_trigger = None
    
    async def _run_iteration(self):
        """Run a single iteration of the test-fix loop."""
        # Check if we should trigger
        if self._should_trigger():
            # Run tests
            result = await self.run_tests()
            
            if result["exit_code"] != 0:
                # Parse failures
                failures = self.parse_test_failures(result["stdout"])
                
                # Process each failure
                for test_name, error in failures.items():
                    if test_name not in self.in_progress_items:
                        await self._handle_test_failure(test_name, error)
            
            # Update state
            self.last_trigger = asyncio.get_event_loop().time()
            self.current_retries = 0
    
    async def _handle_result(self, result: Any):
        """Handle a test result.
        
        Args:
            result: Test result to handle
        """
        if isinstance(result, dict):
            test_name = result.get("test_name")
            success = result.get("success", False)
            
            if test_name in self.in_progress_items:
                self.in_progress_items.remove(test_name)
                
                if success:
                    self.passed_items.add(test_name)
                    if test_name in self.failed_items:
                        self.failed_items.remove(test_name)
                else:
                    self.failed_items.add(test_name)
                    if test_name in self.passed_items:
                        self.passed_items.remove(test_name)
    
    def _should_trigger(self) -> bool:
        """Check if we should trigger a test run.
        
        Returns:
            True if should trigger, False otherwise
        """
        # First run
        if self.last_trigger is None:
            return True
            
        # Check retry limit
        if self.current_retries >= self.max_retries:
            return False
            
        # Check interval
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_trigger >= self.trigger_interval:
            self.current_retries += 1
            return True
            
        return False
    
    async def _handle_test_failure(self, test_name: str, error: str):
        """Handle a test failure.
        
        Args:
            test_name: Name of failed test
            error: Error message
        """
        try:
            # Get test file
            test_file = await self._get_test_file(test_name)
            
            # Determine responsible agent
            agent = self._determine_responsible_agent(test_file)
            
            # Create fix request
            await self.bridge_handler.create_fix_request(
                agent=agent,
                test_name=test_name,
                error=error,
                file_path=str(test_file) if test_file else None
            )
            
            # Track in progress
            self.in_progress_items.add(test_name)
            
        except Exception as e:
            logger.error(f"Error handling test failure: {str(e)}")
    
    async def _get_test_file(self, test_name: str) -> Optional[str]:
        """Get file path for test.
        
        Args:
            test_name: Name of test
            
        Returns:
            Path to test file
        """
        try:
            # Run pytest with --collect-only to get test info
            result = await asyncio.create_subprocess_exec(
                "pytest",
                "--collect-only",
                "-q",
                test_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await result.communicate()
            
            # Parse output to get file path
            for line in stdout.decode().splitlines():
                if test_name in line:
                    parts = line.split("::")
                    if len(parts) >= 2:
                        return parts[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting test file: {str(e)}")
            return None
    
    def _determine_responsible_agent(self, file_path: Optional[str]) -> str:
        """Determine which agent is responsible for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Agent identifier
        """
        if not file_path:
            return "codex"  # Default to codex agent
            
        # Load agent ownership
        try:
            with open("agent_ownership.json") as f:
                ownership = json.load(f)
                
            # Check file path
            for agent, paths in ownership.items():
                if any(file_path.startswith(p) for p in paths):
                    return agent
                    
        except Exception as e:
            logger.error(f"Error loading agent ownership: {str(e)}")
        
        return "codex"  # Default to codex agent 