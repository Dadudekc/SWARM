"""
Fixtures for runner tests.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

@pytest.fixture
def runner_config():
    """Fixture providing a basic runner configuration."""
    return {
        "max_workers": 2,
        "timeout": 30,
        "retry_count": 3,
        "log_level": "INFO"
    }

@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger

@pytest.fixture
def mock_bridge_handler():
    """Fixture providing a mock bridge handler."""
    handler = MagicMock()
    handler.messages = []
    handler.send_message = MagicMock(side_effect=lambda msg: handler.messages.append(msg))
    return handler

@pytest.fixture
def mock_agent_error():
    """Fixture providing a function to create mock agent errors."""
    def _create_error(message):
        error = Exception(message)
        error.agent_id = "test_agent"
        error.timestamp = "2024-03-14T12:00:00Z"
        return error
    return _create_error

@pytest.fixture
def test_data_dir(tmp_path):
    """Fixture providing a temporary directory for test data."""
    return tmp_path

@pytest.fixture
def sample_test_output():
    """Fixture providing sample test output with failures."""
    return """
    ============================= test session starts ==============================
    platform win32 -- Python 3.11.9, pytest-8.4.0, pluggy-1.6.0
    collected 2 items

    test_file.py::test_name FAILED                                         [ 50%]
    test_file2.py::test_name2 FAILED                                      [100%]

    =================================== FAILURES ===================================
    _______________________________ test_name ________________________________
    def test_name():
    >       assert False
    E       assert False

    test_file.py:5: AssertionError
    _______________________________ test_name2 ________________________________
    def test_name2():
    >       assert 1 == 2
    E       assert 1 == 2

    test_file2.py:5: AssertionError
    =========================== short test summary info ============================
    FAILED test_file.py::test_name - assert False
    FAILED test_file2.py::test_name2 - assert 1 == 2
    ============================= 2 failed in 0.12s ==============================
    """

@pytest.fixture
def mock_file_operations():
    """Fixture providing mock file operations."""
    class MockFileOps:
        def __init__(self):
            self.files = {}
        
        def write_file(self, path, content):
            self.files[path] = content
            
        def read_file(self, path):
            return self.files.get(path, "")
            
        def exists(self, path):
            return path in self.files
            
        def remove(self, path):
            if path in self.files:
                del self.files[path]
    
    return MockFileOps()

@pytest.fixture
def runner(runner_config, mock_logger, mock_bridge_handler, mock_file_operations):
    """Fixture providing a configured runner instance."""
    from dreamos.core.autonomy.base.runner_core import RunnerCore
    
    runner = RunnerCore(
        config=runner_config,
        logger=mock_logger,
        bridge_handler=mock_bridge_handler
    )
    
    # Patch file operations
    runner._load_config = lambda path: json.loads(mock_file_operations.read_file(path))
    runner._save_config = lambda path, config: mock_file_operations.write_file(path, json.dumps(config))
    
    return runner 