"""
Autonomy Loop Runner
-------------------
Manages the autonomous test-fix loop by:
1. Running tests and detecting failures
2. Generating repair prompts
3. Injecting them into agent inboxes
4. Monitoring responses and applying fixes
5. Validating fixes and committing changes

Optimized for large-scale projects (3600+ files).
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import pyautogui
import pytest
from concurrent.futures import ThreadPoolExecutor

from ..logging.log_manager import LogManager
from ..messaging.chatgpt_bridge import ChatGPTBridge
from ..agent_loop import AgentLoop, start_agent_loops
from ..agent_control.devlog_manager import DevLogManager
from dreamos.core.autonomy.base.runner_core import RunnerCore
from dreamos.core.autonomy.base.bridge_outbox_handler import BridgeOutboxHandler
from dreamos.core.autonomy.base.response_loop import BaseResponseLoop
from dreamos.core.autonomy.base.state_manager import BaseStateManager
from dreamos.core.autonomy.base.file_handler import BaseFileHandler
from dreamos.core.autonomy.base.runner_lifecycle import RunnerLifecycleMixin
from .bridge.test_devlog_bridge_isolated import TestDevLogBridge
from .error import ErrorTracker, ErrorHandler, ErrorSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock implementation of run_pytest since the actual module is not available
def run_pytest(*args, **kwargs):
    """Mock implementation of run_pytest for testing."""
    print("[MOCK] run_pytest called with", args, kwargs)
    return {"passed": True, "failed": False}

class AutonomyLoopRunner(RunnerCore[str]):
    """Manages the autonomous test-fix loop."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the autonomy loop runner.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config, platform="autonomy_loop")
        
        # Initialize components
        self.bridge_handler = BridgeOutboxHandler()
        self.patch_tracker = CodexPatchTracker()
        self.state_manager = BaseStateManager(self.config)
        
        # Initialize error handling
        self.error_tracker = ErrorTracker()
        self.error_handler = ErrorHandler(self.error_tracker)
        
        # Test-specific configuration
        self.test_dir = self.config.get("test_dir", "tests")
        self.test_pattern = self.config.get("test_pattern", "test_*.py")
        
        # Load agent ownership
        self.agent_ownership = self._load_agent_ownership()
        self.codex_agent = "codex"  # Special agent for quality control
        
        # Set up bridge outbox
        self.bridge_outbox = Path("bridge_outbox")
        self.bridge_outbox.mkdir(exist_ok=True)
        
        # Initialize devlog components
        self.devlog_manager = DevLogManager()
        self.test_bridge = TestDevLogBridge(
            devlog_manager=self.devlog_manager,
            autonomy_runner=self,
            config_path="config/test_devlog_config.json"
        )
        
        self.logger = LogManager()
        self.bridge = ChatGPTBridge(self.config)
        
        # Performance optimization settings
        self.max_workers = self.config.get("max_workers", os.cpu_count() or 4)
        self.chunk_size = self.config.get("chunk_size", 100)  # Files per chunk
        self.test_timeout = self.config.get("test_timeout", 300)  # 5 minutes per test
        self.max_concurrent_tests = self.config.get("max_concurrent_tests", 10)
        
        # Default configuration
        self.test_interval = self.config.get("test_interval", 300)  # 5 minutes
        self.max_retries = self.config.get("max_retries", 3)
        self.commit_message_template = self.config.get(
            "commit_message_template",
            "Agent-X fix: {description}"
        )
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.last_test_time = 0
        self.failed_items = set()
        self.passed_items = set()
        self.in_progress_items = set()
        self.item_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        
        # Thread pool for parallel operations
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Autonomy loop specific settings
        self.loop_interval = self.config.get("loop_interval", 60)  # 1 minute
        self.max_iterations = self.config.get("max_iterations", 10)
        self.iteration_timeout = self.config.get("iteration_timeout", 300)  # 5 minutes
        
        # State tracking
        self.current_iteration = 0
        self.last_iteration = None
        
        # Initialize logging
        self.logger.info(
            platform=self.platform,
            status="initialized",
            message="Autonomy loop runner initialized",
            tags=["init", "autonomy"]
        )
    
    def _load_agent_ownership(self) -> Dict[str, str]:
        """Load agent ownership mapping.
        
        Returns:
            Dictionary mapping file paths to agent IDs
        """
        try:
            with open("config/agent_ownership.json", 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    async def start(self):
        """Start the autonomy loop."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start the agent loop in the background
        self.agent_loop_task = asyncio.create_task(start_agent_loops())
        
        # Start the main worker loop
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform=self.platform,
            status="started",
            message="Autonomy loop started",
            tags=["start", "autonomy"]
        )
    
    async def stop(self):
        """Stop the autonomy loop."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Cancel both tasks
        if self.agent_loop_task:
            self.agent_loop_task.cancel()
            try:
                await self.agent_loop_task
            except asyncio.CancelledError:
                pass
                
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform=self.platform,
            status="stopped",
            message="Autonomy loop stopped",
            tags=["stop", "autonomy"]
        )
    
    async def _worker_loop(self):
        """Main worker loop for autonomy."""
        while self.is_running:
            try:
                # Check if we should run iteration
                if self._should_run_iteration():
                    # Run tests with retry
                    result = await self.error_handler.with_retry(
                        operation="run_tests",
                        agent_id=self.platform,
                        func=self.run_tests
                    )
                    
                    if result["exit_code"] != 0:
                        # Parse failures
                        failures = self.parse_test_failures(result["stdout"])
                        
                        # Process each failure
                        for test_name, error in failures.items():
                            if test_name not in self.in_progress_items:
                                await self._handle_test_failure(test_name, error)
                    
                    # Update state
                    self.last_iteration = asyncio.get_event_loop().time()
                    self.current_iteration += 1
                
                # Wait for next check
                await asyncio.sleep(self.loop_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_tracker.record_error(
                    error_type=type(e).__name__,
                    message=str(e),
                    severity=ErrorSeverity.HIGH,
                    agent_id=self.platform,
                    context={"operation": "worker_loop"}
                )
                await asyncio.sleep(5)  # Back off on error
    
    def _should_run_iteration(self) -> bool:
        """Check if we should run an iteration.
        
        Returns:
            True if should run, False otherwise
        """
        # Check iteration limit
        if self.current_iteration >= self.max_iterations:
            return False
            
        # First run
        if self.last_iteration is None:
            return True
            
        # Check interval
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_iteration >= self.loop_interval:
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
            
            # Create fix request with retry
            await self.error_handler.with_retry(
                operation="create_fix_request",
                agent_id=agent,
                func=self.bridge_handler.create_fix_request,
                agent=agent,
                test_name=test_name,
                error=error,
                file_path=str(test_file) if test_file else None
            )
            
            # Track in progress
            self.in_progress_items.add(test_name)
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=self.platform,
                context={
                    "operation": "handle_test_failure",
                    "test_name": test_name,
                    "error": error
                }
            )
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
    
    def generate_fix_prompt(self, test_name: str, error: str) -> str:
        """Generate a prompt for fixing a test.
        
        Args:
            test_name: Name of the test
            error: Error message
            
        Returns:
            Generated prompt
        """
        return f"""Please fix the following test failure:

Test: {test_name}
Error: {error}

Please provide a complete fix that:
1. Addresses the root cause
2. Maintains existing functionality
3. Follows project style guidelines
4. Includes necessary imports
5. Handles edge cases

Respond with the complete fixed code."""
    
    async def escalate_to_codex(self, agent_id: str, file_path: str, test_name: str, error: str, response: str):
        """Escalate a failed fix to Codex.
        
        Args:
            agent_id: Original agent ID
            file_path: Path to the file
            test_name: Name of the test
            error: Error message
            response: Failed fix response
        """
        prompt = f"""Agent {agent_id} attempted to fix test {test_name} but failed:

Original Error: {error}
Failed Fix: {response}

Please provide a complete fix that:
1. Addresses the root cause
2. Maintains existing functionality
3. Follows project style guidelines
4. Includes necessary imports
5. Handles edge cases

Respond with the complete fixed code."""
        
        await self.inject_prompt_to_agent(self.codex_agent, prompt)
    
    def apply_code_patch(self, file_path: str, response: str) -> bool:
        """Apply a code patch.
        
        Args:
            file_path: Path to the file
            response: Code to apply
            
        Returns:
            True if patch applied successfully, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                f.write(response)
            return True
            
        except Exception as e:
            self.logger.error(
                platform=self.platform,
                status="error",
                message=f"Error applying patch: {str(e)}",
                tags=["patch", "error"]
            )
            return False
    
    async def test_passes(self, test_name: str) -> bool:
        """Check if a test passes.
        
        Args:
            test_name: Name of the test
            
        Returns:
            True if test passes, False otherwise
        """
        try:
            result = await self.error_handler.with_retry(
                operation="test_passes",
                agent_id=self.platform,
                func=self._run_test,
                test_name=test_name
            )
            return result
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=self.platform,
                context={"operation": "test_passes", "test_name": test_name}
            )
            return False
    
    async def _run_test(self, test_name: str) -> bool:
        """Run a single test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            True if test passes, False otherwise
        """
        result = await asyncio.create_subprocess_exec(
            "pytest",
            test_name,
            "-v",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        return result.returncode == 0
    
    def commit_code(self, file_path: str, message: str):
        """Commit code changes.
        
        Args:
            file_path: Path to the file
            message: Commit message
        """
        try:
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", message], check=True)
            
            self.logger.info(
                platform=self.platform,
                status="success",
                message=f"Committed changes to {file_path}",
                tags=["commit", "success"]
            )
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id=self.platform,
                context={
                    "operation": "commit_code",
                    "file_path": file_path,
                    "message": message
                }
            )
            self.logger.error(
                platform=self.platform,
                status="error",
                message=f"Error committing changes: {str(e)}",
                tags=["commit", "error"]
            )
    
    async def _run_iteration(self):
        """Run a single iteration of the test-fix loop."""
        # Check if we should run iteration
        if self._should_run_iteration():
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
            self.last_iteration = asyncio.get_event_loop().time()
            self.current_iteration += 1
    
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
    
    async def _get_test_files(self) -> List[str]:
        """Get list of test files to run.
        
        Returns:
            List of test file paths
        """
        # Implementation specific to test framework
        return [] 