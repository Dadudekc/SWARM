"""
Runner Test Fixtures
------------------
Shared fixtures for runner tests.
"""

import asyncio
import json
import logging
import os
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from dreamos.core.autonomy.base.runner_core import RunnerCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRunner(RunnerCore[str]):
    """Test implementation of RunnerCore."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize test runner."""
        super().__init__(config, platform="test_runner")
        self.test_items = ["test1", "test2", "test3"]
        self.processed_items = []
    
    async def _run_iteration(self):
        """Run a test iteration."""
        for item in self.test_items:
            if item not in self.in_progress_items:
                await self.item_queue.put(item)
                self.in_progress_items.add(item)
    
    async def _handle_result(self, result: Any):
        """Handle a test result."""
        if isinstance(result, dict):
            item = result.get("item")
            success = result.get("success", False)
            
            if item in self.in_progress_items:
                self.in_progress_items.remove(item)
                self.processed_items.append(item)
                
                if success:
                    self.passed_items.add(item)
                    if item in self.failed_items:
                        self.failed_items.remove(item)
                else:
                    self.failed_items.add(item)
                    if item in self.passed_items:
                        self.passed_items.remove(item)

@pytest.fixture
def runner_config():
    """Base configuration for runner tests."""
    return {
        "check_interval": 0.1,  # 100ms for faster tests
        "max_retries": 2,
        "test_interval": 0.2,  # 200ms for faster tests
        "max_workers": 2,
        "chunk_size": 10,
        "test_timeout": 1,  # 1 second for faster tests
        "max_concurrent_tests": 2
    }

@pytest.fixture
async def runner(runner_config):
    """Test runner instance."""
    runner = TestRunner(runner_config)
    yield runner
    await runner.stop()

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    class MockLogger:
        def __init__(self):
            self.logs = []
            self.errors = []
        
        def info(self, *args, **kwargs):
            self.logs.append(("info", args, kwargs))
        
        def error(self, *args, **kwargs):
            self.errors.append(("error", args, kwargs))
        
        def warning(self, *args, **kwargs):
            self.logs.append(("warning", args, kwargs))
        
        def debug(self, *args, **kwargs):
            self.logs.append(("debug", args, kwargs))
    
    return MockLogger()

@pytest.fixture
def mock_bridge_handler():
    """Mock bridge handler for testing."""
    class MockBridgeHandler:
        def __init__(self):
            self.messages = []
            self.responses = {}
        
        async def send_message(self, message: str, **kwargs):
            self.messages.append(message)
            return self.responses.get(message, "default_response")
        
        def set_response(self, message: str, response: str):
            self.responses[message] = response
    
    return MockBridgeHandler()

@pytest.fixture
def mock_agent_error():
    """Mock agent error for testing."""
    class MockAgentError(Exception):
        def __init__(self, message: str, code: str = "TEST_ERROR"):
            super().__init__(message)
            self.code = code
            self.timestamp = datetime.now()
    
    return MockAgentError

@pytest.fixture
def test_data_dir(tmp_path):
    """Temporary test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_test_output():
    """Sample test output for parsing tests."""
    return """
    FAILED test_file.py::test_name - AssertionError: Test failed
    FAILED test_file2.py::test_name2 - ValueError: Invalid value
    PASSED test_file3.py::test_name3
    """

@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    class MockFileOps:
        def __init__(self):
            self.files = {}
            self.deleted = set()
        
        def write_file(self, path: str, content: str):
            self.files[path] = content
        
        def read_file(self, path: str) -> str:
            return self.files.get(path, "")
        
        def delete_file(self, path: str):
            self.deleted.add(path)
            if path in self.files:
                del self.files[path]
        
        def file_exists(self, path: str) -> bool:
            return path in self.files
    
    return MockFileOps() 