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
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import pyautogui
import pytest
from concurrent.futures import ThreadPoolExecutor

from ..logging.log_manager import LogManager
from ..messaging.chatgpt_bridge import ChatGPTBridge
from ..agent_loop import AgentLoop
from ...tests.utils.init_feedback_loop import run_pytest
from .test_devlog_bridge import TestDevLogBridge
from .devlog_manager import DevLogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomyLoopRunner:
    """Manages the autonomous test-fix loop."""
    
    def __init__(self, config_path: str = "config/autonomy_config.json"):
        """Initialize the autonomy loop runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.agent_ownership = self._load_agent_ownership()
        self.codex_agent = "codex"  # Special agent for quality control
        self.bridge_outbox = Path("bridge_outbox")
        self.bridge_outbox.mkdir(exist_ok=True)
        
        # Initialize devlog components
        self.devlog_manager = DevLogManager()
        self.test_devlog_bridge = TestDevLogBridge(
            devlog_manager=self.devlog_manager,
            autonomy_runner=self
        )
        
        self.logger = LogManager()
        self.bridge = ChatGPTBridge(self.config)
        self.agent_loop = AgentLoop()
        
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
        self.failed_tests = set()
        self.passed_tests = set()
        self.in_progress_tests = set()
        self.test_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        
        # Thread pool for parallel operations
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Initialize logging
        self.logger.info(
            platform="autonomy_loop",
            status="initialized",
            message="Autonomy loop runner initialized",
            tags=["init", "autonomy"]
        )
    
    async def start(self):
        """Start the autonomy loop."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform="autonomy_loop",
            status="started",
            message="Autonomy loop started",
            tags=["start", "autonomy"]
        )
    
    async def stop(self):
        """Stop the autonomy loop."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform="autonomy_loop",
            status="stopped",
            message="Autonomy loop stopped",
            tags=["stop", "autonomy"]
        )
    
    async def _run_tests(self) -> Dict[str, Any]:
        """Run pytest and collect results with optimized parallel execution."""
        try:
            # Get list of test files
            test_files = self._get_test_files()
            
            # Split into chunks for parallel processing
            chunks = self._chunk_test_files(test_files)
            
            # Create tasks for each chunk
            tasks = []
            for chunk in chunks:
                task = asyncio.create_task(
                    self._run_test_chunk(chunk)
                )
                tasks.append(task)
            
            # Wait for all chunks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_results = self._combine_test_results(results)
            
            # Log test run results
            await self.test_devlog_bridge.log_test_run(combined_results)
            
            if combined_results['exit_code'] != 0:
                self.logger.warning(
                    platform="autonomy_loop",
                    status="test_failure",
                    message="Tests failed, analyzing failures",
                    tags=["test", "failure"]
                )
                
                # Parse test output to identify failures
                failed_tests = self._parse_test_failures(combined_results['stdout'])
                self.failed_tests.update(failed_tests)
                
                # Generate repair prompts for each failure
                for test_name, error in failed_tests.items():
                    await self._handle_test_failure(test_name, error)
            
            return combined_results
            
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error running tests: {str(e)}",
                tags=["test", "error"]
            )
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def _get_test_files(self) -> List[str]:
        """Get list of test files to run."""
        try:
            # Use pytest to collect test files
            result = subprocess.run(
                ["pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True
            )
            
            # Parse output to get test files
            test_files = []
            for line in result.stdout.split('\n'):
                if line.startswith('tests/'):
                    test_files.append(line.split('::')[0])
            
            return list(set(test_files))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error getting test files: {e}")
            return []
    
    def _chunk_test_files(self, test_files: List[str]) -> List[List[str]]:
        """Split test files into chunks for parallel processing."""
        chunks = []
        current_chunk = []
        
        for test_file in test_files:
            current_chunk.append(test_file)
            if len(current_chunk) >= self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = []
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _run_test_chunk(self, chunk: List[str]) -> Dict[str, Any]:
        """Run a chunk of test files."""
        try:
            # Run pytest on chunk with timeout
            process = await asyncio.create_subprocess_exec(
                "pytest",
                *chunk,
                "-v",
                "--json-report",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.test_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': f'Test chunk timed out after {self.test_timeout}s'
                }
            
            return {
                'exit_code': process.returncode,
                'stdout': stdout.decode(),
                'stderr': stderr.decode()
            }
            
        except Exception as e:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def _combine_test_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine results from multiple test chunks."""
        combined = {
            'exit_code': 0,
            'stdout': '',
            'stderr': '',
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for result in results:
            if isinstance(result, Exception):
                combined['exit_code'] = -1
                combined['stderr'] += f"Error: {str(result)}\n"
                continue
                
            if result['exit_code'] != 0:
                combined['exit_code'] = result['exit_code']
            
            combined['stdout'] += result['stdout']
            combined['stderr'] += result['stderr']
            
            # Parse test counts from output
            for line in result['stdout'].split('\n'):
                if 'passed' in line:
                    combined['passed'] += int(line.split()[0])
                elif 'failed' in line:
                    combined['failed'] += int(line.split()[0])
                elif 'skipped' in line:
                    combined['skipped'] += int(line.split()[0])
        
        combined['total'] = combined['passed'] + combined['failed'] + combined['skipped']
        return combined
    
    def _parse_test_failures(self, test_output: str) -> Dict[str, str]:
        """Parse pytest output to identify failed tests.
        
        Args:
            test_output: Raw pytest output
            
        Returns:
            Dictionary mapping test names to error messages
        """
        failures = {}
        current_test = None
        error_buffer = []
        
        for line in test_output.split('\n'):
            if line.startswith('FAILED '):
                # Extract test name
                test_name = line.split('::')[-1].strip()
                current_test = test_name
                error_buffer = []
            elif current_test and line.strip():
                error_buffer.append(line)
                if 'AssertionError' in line or 'Exception' in line:
                    failures[current_test] = '\n'.join(error_buffer)
                    current_test = None
        
        return failures
    
    async def _handle_test_failure(self, test_name: str, error: str) -> None:
        """Handle a test failure.
        
        Args:
            test_name: Name of failed test
            error: Error message
        """
        try:
            # Get agent for test
            agent_id = self._get_agent_for_test(test_name)
            
            # Generate fix prompt
            prompt = self._generate_fix_prompt(test_name, error)
            
            # Send to agent
            fix = await self._send_to_agent(agent_id, prompt)
            
            # Validate fix
            success, validation_error = await self._validate_fix(test_name, fix)
            
            # Log fix attempt
            await self.test_devlog_bridge.log_fix_attempt(
                test_name=test_name,
                agent_id=agent_id,
                fix=fix,
                success=success,
                error=validation_error
            )
            
            if not success:
                # Escalate to Codex if fix failed
                await self._escalate_to_codex(test_name, error, fix, validation_error)
                
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error handling test failure: {str(e)}",
                tags=["test", "error"]
            )
    
    def _generate_fix_prompt(self, test_name: str, error: str) -> str:
        """Generate a fix prompt for a failed test.
        
        Args:
            test_name: Name of failed test
            error: Error message from test
            
        Returns:
            Formatted fix prompt
        """
        return f"""Fix the bug in the test '{test_name}'. Here's the error:

{error}

Please:
1. Analyze the error
2. Identify the root cause
3. Propose a fix
4. Include the exact code changes needed
5. Explain why the fix works

Format your response as:
```python
# File: path/to/file.py
# Changes:
{{code changes}}
```

Then explain your fix."""

    async def _apply_fix(self, response: str) -> bool:
        """Apply a code fix from ChatGPT response.
        
        Args:
            response: ChatGPT response containing fix
            
        Returns:
            True if fix was applied successfully
        """
        try:
            # Parse code changes from response
            changes = self._parse_code_changes(response)
            if not changes:
                return False
            
            # Apply changes to files
            for file_path, code_changes in changes.items():
                self._apply_file_changes(file_path, code_changes)
            
            # Run tests to verify fix
            results = await self._run_tests()
            if results['exit_code'] == 0:
                # Commit changes
                self._commit_changes(response)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error applying fix: {str(e)}",
                tags=["fix", "error"]
            )
            return False
    
    def _parse_code_changes(self, response: str) -> Dict[str, str]:
        """Parse code changes from ChatGPT response.
        
        Args:
            response: ChatGPT response containing fix
            
        Returns:
            Dictionary mapping file paths to code changes
        """
        changes = {}
        current_file = None
        code_buffer = []
        
        for line in response.split('\n'):
            if line.startswith('# File:'):
                if current_file and code_buffer:
                    changes[current_file] = '\n'.join(code_buffer)
                current_file = line.split(':', 1)[1].strip()
                code_buffer = []
            elif current_file and line.strip():
                code_buffer.append(line)
        
        if current_file and code_buffer:
            changes[current_file] = '\n'.join(code_buffer)
        
        return changes
    
    def _apply_file_changes(self, file_path: str, changes: str):
        """Apply code changes to a file.
        
        Args:
            file_path: Path to file to modify
            changes: Code changes to apply
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply changes (simple string replacement for now)
            # TODO: Use AST for more robust changes
            new_content = content.replace(
                self._extract_original_code(content, changes),
                changes
            )
            
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.logger.info(
                platform="autonomy_loop",
                status="success",
                message=f"Applied changes to {file_path}",
                tags=["fix", "apply"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error applying changes to {file_path}: {str(e)}",
                tags=["fix", "error"]
            )
            raise
    
    def _extract_original_code(self, content: str, changes: str) -> str:
        """Extract the original code that needs to be changed.
        
        Args:
            content: Original file content
            changes: New code changes
            
        Returns:
            Original code to replace
        """
        # TODO: Implement smarter code matching
        # For now, just return the first matching function/class
        lines = changes.split('\n')
        if not lines:
            return ""
            
        # Find the first non-empty line
        first_line = next((l for l in lines if l.strip()), "")
        if not first_line:
            return ""
            
        # Find matching function/class in original content
        for line in content.split('\n'):
            if first_line in line:
                # Return the entire function/class
                return line
        
        return ""
    
    def _commit_changes(self, response: str):
        """Commit code changes.
        
        Args:
            response: ChatGPT response containing fix
        """
        try:
            # Extract description from response
            description = response.split('\n\n')[-1].strip()
            if len(description) > 100:
                description = description[:97] + "..."
            
            # Create commit message
            commit_msg = self.commit_message_template.format(
                description=description
            )
            
            # Run git commit
            subprocess.run([
                "git", "add", ".",
                "git", "commit", "-m", commit_msg
            ], check=True)
            
            self.logger.info(
                platform="autonomy_loop",
                status="success",
                message=f"Committed changes: {commit_msg}",
                tags=["commit", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error committing changes: {str(e)}",
                tags=["commit", "error"]
            )
            raise
    
    async def _worker_loop(self):
        """Main worker loop for autonomy system."""
        while self.is_running:
            try:
                current_time = time.time()
                
                # Check if it's time to run tests
                if current_time - self.last_test_time >= self.test_interval:
                    await self._run_tests()
                    self.last_test_time = current_time
                
                # Process any pending fixes
                if self.failed_tests:
                    # TODO: Check for responses from ChatGPT bridge
                    # and apply fixes
                    pass
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    platform="autonomy_loop",
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["worker", "error"]
                )
                await asyncio.sleep(5)  # Back off on error 

    async def _update_test_progress(self) -> None:
        """Update test progress."""
        try:
            status = {
                "total_tests": len(self.failed_tests) + len(self.passed_tests),
                "passed": len(self.passed_tests),
                "failed": len(self.failed_tests),
                "skipped": 0,
                "in_progress": len(self.in_progress_tests)
            }
            
            await self.test_devlog_bridge.log_test_progress(status)
            
        except Exception as e:
            self.logger.error(
                platform="autonomy_loop",
                status="error",
                message=f"Error updating test progress: {str(e)}",
                tags=["test", "error"]
            ) 