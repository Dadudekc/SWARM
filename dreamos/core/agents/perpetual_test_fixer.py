"""
Perpetual Test Fixer
------------------
Coordinates test failures with agents and Codex validation:
1. Runs pytest continuously
2. Routes failures to appropriate agents
3. Validates fixes through Codex
4. Tracks agent assignments
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pytest
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..codex.codex_quality_controller import CodexController
from ..logging.log_manager import LogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFailureHandler(FileSystemEventHandler):
    """Handles test file changes and triggers test runs."""
    
    def __init__(self, test_fixer):
        self.test_fixer = test_fixer
        
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            asyncio.create_task(self.test_fixer.run_tests())

class PerpetualTestFixer:
    """Coordinates test failures with agents and Codex validation."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the test fixer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        
        # Initialize components
        self.codex = CodexController(config)
        
        # Track state
        self.failing_tests: Dict[str, List[str]] = {}  # test_file -> [test_names]
        self.agent_assignments: Dict[str, str] = {}  # test_file -> agent_id
        self.fixed_tests: Set[str] = set()
        
        # Setup file watcher
        self.observer = Observer()
        self.observer.schedule(
            TestFailureHandler(self),
            path=".",
            recursive=True
        )
        
        # Initialize logging
        self.logger.info(
            platform="test_fixer",
            status="initialized",
            message="Perpetual test fixer initialized",
            tags=["init", "test_fixer"]
        )
        
    async def start(self):
        """Start the test fixer."""
        try:
            # Start Codex
            await self.codex.start()
            
            # Start file watcher
            self.observer.start()
            
            # Run initial test suite
            await self.run_tests()
            
            self.logger.info(
                platform="test_fixer",
                status="started",
                message="Perpetual test fixer started",
                tags=["start", "test_fixer"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="test_fixer",
                status="error",
                message=f"Error starting test fixer: {str(e)}",
                tags=["start", "error"]
            )
            raise
            
    async def stop(self):
        """Stop the test fixer."""
        try:
            # Stop file watcher
            self.observer.stop()
            self.observer.join()
            
            # Stop Codex
            await self.codex.stop()
            
            self.logger.info(
                platform="test_fixer",
                status="stopped",
                message="Perpetual test fixer stopped",
                tags=["stop", "test_fixer"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="test_fixer",
                status="error",
                message=f"Error stopping test fixer: {str(e)}",
                tags=["stop", "error"]
            )
            
    async def run_tests(self) -> bool:
        """Run pytest and process failures.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            # Run pytest
            process = await asyncio.create_subprocess_exec(
                "pytest",
                "-v",
                "--json-report",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Parse test results
            if process.returncode == 0:
                self.failing_tests.clear()
                self.agent_assignments.clear()
                self.fixed_tests.clear()
                return True
                
            # Process failures
            report = json.loads(stdout)
            self._process_failures(report)
            
            # Route failures to agents
            await self._route_failures()
            
            return False
            
        except Exception as e:
            self.logger.error(
                platform="test_fixer",
                status="error",
                message=f"Error running tests: {str(e)}",
                tags=["test", "error"]
            )
            return False
            
    def _process_failures(self, report: Dict):
        """Process pytest failure report."""
        for test in report.get("tests", []):
            if test.get("outcome") == "failed":
                test_file = test.get("nodeid", "").split("::")[0]
                test_name = test.get("nodeid", "").split("::")[-1]
                
                if test_file not in self.failing_tests:
                    self.failing_tests[test_file] = []
                self.failing_tests[test_file].append(test_name)
                
    async def _route_failures(self):
        """Route test failures to appropriate agents."""
        for test_file, test_names in self.failing_tests.items():
            # Skip if already assigned
            if test_file in self.agent_assignments:
                continue
                
            # Find available agent
            agent_id = await self._get_available_agent()
            if not agent_id:
                continue
                
            # Assign test to agent
            self.agent_assignments[test_file] = agent_id
            
            # Get agent's debug prompt
            prompt = await self._get_agent_prompt(agent_id, test_file, test_names)
            
            # Send prompt to agent
            await self._send_to_agent(agent_id, prompt)
            
    async def _get_available_agent(self) -> Optional[str]:
        """Get next available agent ID."""
        # Simple round-robin for now
        assigned_agents = set(self.agent_assignments.values())
        all_agents = {"agent1", "agent2", "agent3", "agent4"}
        available = all_agents - assigned_agents
        return next(iter(available)) if available else None
        
    async def _get_agent_prompt(self, agent_id: str, test_file: str, test_names: List[str]) -> str:
        """Get debug prompt for agent."""
        return f"""
Debug prompt for {agent_id}:

Test file: {test_file}
Failing tests: {', '.join(test_names)}

Please analyze and fix the failing tests.
"""
        
    async def _send_to_agent(self, agent_id: str, prompt: str):
        """Send prompt to agent."""
        # TODO: Implement actual agent communication
        self.logger.info(
            platform="test_fixer",
            status="sent",
            message=f"Sent prompt to {agent_id}",
            tags=["agent", "prompt"]
        )
        
    async def process_agent_response(self, agent_id: str, test_file: str, response: str) -> bool:
        """Process response from agent.
        
        Args:
            agent_id: ID of responding agent
            test_file: Test file being fixed
            response: Agent's proposed fix
            
        Returns:
            True if fix was successful, False otherwise
        """
        try:
            # Validate through Codex
            success, error = await self.codex.validate_and_patch(test_file, response)
            
            if not success:
                self.logger.warning(
                    platform="test_fixer",
                    status="invalid",
                    message=f"Invalid fix from {agent_id}: {error}",
                    tags=["agent", "fix"]
                )
                return False
                
            # Run tests again
            if await self.run_tests():
                # Fix successful
                self.fixed_tests.add(test_file)
                del self.agent_assignments[test_file]
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(
                platform="test_fixer",
                status="error",
                message=f"Error processing agent response: {str(e)}",
                tags=["agent", "error"]
            )
            return False
            
    def get_status(self) -> Dict:
        """Get current status of test fixer."""
        return {
            "failing_tests": self.failing_tests,
            "agent_assignments": self.agent_assignments,
            "fixed_tests": list(self.fixed_tests)
        } 
