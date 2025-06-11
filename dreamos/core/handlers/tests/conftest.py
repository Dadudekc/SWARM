"""
Test Configuration
---------------
Configuration for handler tests.
"""

import pytest
import asyncio
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_dir(tmp_path_factory):
    """Create a temporary test directory."""
    return tmp_path_factory.mktemp("handler_tests")

@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    return {
        "name": "test_handler",
        "max_retries": 3,
        "retry_delay": 0.1,
        "test_data": {
            "key": "value"
        }
    } 