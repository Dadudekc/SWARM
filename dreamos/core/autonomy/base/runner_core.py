"""
Runner Core
----------
Provides unified core functionality for all autonomous runners.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Protocol, TypeVar, Generic

from ..logging.log_manager import LogManager
from ...utils.testing_utils import parse_test_failures as parse_failures

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')

class RunnerConfig(Protocol):
    """Protocol for runner configuration."""
    check_interval: int
    max_retries: int
    test_interval: int
    max_workers: int
    chunk_size: int
    test_timeout: int
    max_concurrent_tests: int

class RunnerCore(Generic[T]):
    """Base class for all runners with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, platform: Optional[str] = None):
        """Initialize the runner core.
        
        Args:
            config: Optional configuration dictionary
            platform: Optional platform identifier
        """
        self.config = config or {}
        self.platform = platform or self.__class__.__name__
        self.logger = LogManager()
        
        # Default configuration
        self.check_interval = self.config.get("check_interval", 5)  # 5 seconds
        self.max_retries = self.config.get("max_retries", 3)
        self.test_interval = self.config.get("test_interval", 300)  # 5 minutes
        self.max_workers = self.config.get("max_workers", 4)
        self.chunk_size = self.config.get("chunk_size", 100)
        self.test_timeout = self.config.get("test_timeout", 300)  # 5 minutes
        self.max_concurrent_tests = self.config.get("max_concurrent_tests", 10)
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.last_run_time = 0
        self.failed_items: Set[T] = set()
        self.passed_items: Set[T] = set()
        self.in_progress_items: Set[T] = set()
        self.item_queue: asyncio.Queue[T] = asyncio.Queue()
        self.result_queue: asyncio.Queue[Any] = asyncio.Queue()
        
        # Initialize logging
        self.logger.info(f"[{self.platform}] {self.__class__.__name__} initialized [init, runner]")
    
    async def start(self):
        """Start the runner."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(f"[{self.platform}] {self.__class__.__name__} started [start, runner]")
    
    async def stop(self):
        """Stop the runner."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(f"[{self.platform}] {self.__class__.__name__} stopped [stop, runner]")
    
    async def _worker_loop(self):
        """Main worker loop for the runner."""
        while self.is_running:
            try:
                # Check if it's time to run
                current_time = datetime.now().timestamp()
                if current_time - self.last_run_time >= self.test_interval:
                    await self._run_iteration()
                    self.last_run_time = current_time
                
                # Process results
                while not self.result_queue.empty():
                    result = await self.result_queue.get()
                    await self._handle_result(result)
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"[{self.platform}] Error in worker loop: {str(e)} [worker, error]")
                await asyncio.sleep(5)  # Back off on error
    
    async def _run_iteration(self):
        """Run a single iteration of the runner's main task."""
        raise NotImplementedError("Subclasses must implement _run_iteration")
    
    async def _handle_result(self, result: Any):
        """Handle a result from the runner's task.
        
        Args:
            result: Result to handle
        """
        raise NotImplementedError("Subclasses must implement _handle_result")
    
    async def _run_with_timeout(self, coro, timeout: int) -> Optional[Any]:
        """Run a coroutine with a timeout.
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            
        Returns:
            Result of the coroutine or None if timed out
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"[{self.platform}] Operation timed out after {timeout} seconds [timeout]")
            return None
        except Exception as e:
            self.logger.error(f"[{self.platform}] Error in operation: {str(e)} [error]")
            return None
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"[{self.platform}] Error loading config: {str(e)} [config, error]")
            return {}
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run test suite and return results.
        
        Returns:
            Dictionary containing test results
        """
        try:
            # Run pytest with coverage
            result = await asyncio.create_subprocess_exec(
                "pytest",
                "--cov=.",
                "--cov-report=term-missing",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return {
                "exit_code": result.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
            
        except Exception as e:
            self.logger.error(f"[{self.platform}] Error running tests: {str(e)} [test, error]")
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def parse_test_failures(self, output: str) -> Dict[str, str]:
        """Parse test failures from pytest output."""
        return parse_failures(output)
