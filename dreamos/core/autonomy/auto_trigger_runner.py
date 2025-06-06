"""AutoTriggerRunner - Manages automatic test failure handling and fix loops."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..logging.log_manager import LogManager
from .autonomy_loop_runner import AutonomyLoopRunner
from .bridge_outbox_handler import BridgeOutboxHandler
from .codex_patch_tracker import CodexPatchTracker

class AutoTriggerRunner:
    """Manages automatic test failure handling and fix loops."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the auto trigger runner.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        
        # Initialize components
        self.autonomy_loop = AutonomyLoopRunner()
        self.bridge_handler = BridgeOutboxHandler()
        self.patch_tracker = CodexPatchTracker()
        
        # Default configuration
        self.check_interval = self.config.get("check_interval", 5)  # 5 seconds
        self.max_retries = self.config.get("max_retries", 3)
        self.test_analysis_file = Path(self.config.get("test_analysis_file", "test_error_analysis.json"))
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.processing_tests = set()
        
        # Initialize logging
        self.logger.info(
            platform="auto_trigger",
            status="initialized",
            message="Auto trigger runner initialized",
            tags=["init", "trigger"]
        )
    
    async def start(self):
        """Start the auto trigger runner."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform="auto_trigger",
            status="started",
            message="Auto trigger runner started",
            tags=["start", "trigger"]
        )
    
    async def stop(self):
        """Stop the auto trigger runner."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            
        self.logger.info(
            platform="auto_trigger",
            status="stopped",
            message="Auto trigger runner stopped",
            tags=["stop", "trigger"]
        )
    
    async def _worker_loop(self):
        """Main worker loop for auto trigger runner."""
        while self.is_running:
            try:
                # Check for test failures
                test_results = await self.autonomy_loop._run_tests()
                
                if test_results['exit_code'] != 0:
                    # Parse test output to identify failures
                    failed_tests = self.autonomy_loop._parse_test_failures(test_results['stdout'])
                    
                    # Process each failure
                    for test_name, error in failed_tests.items():
                        if test_name not in self.processing_tests:
                            await self._handle_test_failure(test_name, error)
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    platform="auto_trigger",
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["worker", "error"]
                )
                await asyncio.sleep(5)  # Back off on error
    
    async def _handle_test_failure(self, test_name: str, error: str):
        """Handle a test failure.
        
        Args:
            test_name: Name of the failed test
            error: Error message from test
        """
        try:
            # Mark test as being processed
            self.processing_tests.add(test_name)
            
            # Update test analysis
            await self._update_test_analysis(test_name, error)
            
            # Generate repair prompt
            prompt = await self._generate_repair_prompt(test_name, error)
            
            # Inject prompt to agent
            agent_id = await self._assign_agent(test_name)
            await self.autonomy_loop.inject_prompt_to_agent(agent_id, prompt)
            
            # Wait for response
            if await self.autonomy_loop.wait_for_reply(agent_id):
                response = self.autonomy_loop.retrieve_response(agent_id)
                
                if response:
                    # Validate with Codex
                    if await self.autonomy_loop.is_valid_code(response):
                        # Apply patch
                        await self.bridge_handler._process_response({
                            "id": f"{test_name}-{datetime.utcnow().isoformat()}",
                            "response": response,
                            "test_name": test_name
                        })
                        
                        # Re-run test
                        await self._verify_fix(test_name)
            
        except Exception as e:
            self.logger.error(
                platform="auto_trigger",
                status="error",
                message=f"Error handling test failure {test_name}: {str(e)}",
                tags=["failure", "error"]
            )
        finally:
            self.processing_tests.remove(test_name)
    
    async def _update_test_analysis(self, test_name: str, error: str):
        """Update test analysis data.
        
        Args:
            test_name: Name of the test
            error: Error message
        """
        try:
            if not self.test_analysis_file.exists():
                data = {
                    "claimed_tests": {},
                    "test_status": {
                        "total_tests": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "in_progress": 0
                    }
                }
            else:
                with open(self.test_analysis_file, 'r') as f:
                    data = json.load(f)
            
            # Update test status
            data["test_status"]["failed"] += 1
            data["test_status"]["in_progress"] += 1
            
            # Add test to claimed tests
            data["claimed_tests"][test_name] = {
                "status": "in_progress",
                "error": error,
                "claimed_at": datetime.utcnow().isoformat(),
                "fix_attempts": []
            }
            
            # Save updated data
            with open(self.test_analysis_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(
                platform="auto_trigger",
                status="error",
                message=f"Error updating test analysis: {str(e)}",
                tags=["analysis", "error"]
            )
    
    async def _generate_repair_prompt(self, test_name: str, error: str) -> str:
        """Generate repair prompt for agent.
        
        Args:
            test_name: Name of the test
            error: Error message
            
        Returns:
            Generated prompt
        """
        return f"""Please fix the failing test {test_name}.
Error: {error}

Requirements:
1. Fix must be minimal and focused
2. Must maintain existing functionality
3. Must follow project coding standards
4. Must include test case

Please provide the complete fix as a code block."""

    async def _assign_agent(self, test_name: str) -> str:
        """Assign an agent to fix the test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Assigned agent ID
        """
        # For now, use a simple round-robin assignment
        # TODO: Implement smarter agent selection based on expertise
        return "Agent-1"
    
    async def _verify_fix(self, test_name: str):
        """Verify that a fix resolved the test failure.
        
        Args:
            test_name: Name of the test
        """
        try:
            # Run the specific test
            result = await self.autonomy_loop._run_test_chunk([test_name])
            
            # Update test analysis
            with open(self.test_analysis_file, 'r') as f:
                data = json.load(f)
            
            if result['exit_code'] == 0:
                # Test passed
                data["test_status"]["passed"] += 1
                data["test_status"]["failed"] -= 1
                data["claimed_tests"][test_name]["status"] = "completed"
            else:
                # Test still failing
                data["claimed_tests"][test_name]["fix_attempts"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": result['stdout']
                })
            
            data["test_status"]["in_progress"] -= 1
            
            # Save updated data
            with open(self.test_analysis_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(
                platform="auto_trigger",
                status="error",
                message=f"Error verifying fix for {test_name}: {str(e)}",
                tags=["verify", "error"]
            ) 