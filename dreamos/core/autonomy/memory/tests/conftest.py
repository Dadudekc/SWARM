"""
Pytest configuration for memory tracker tests
-------------------------------------------
"""

import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    return {
        "paths": {
            "runtime": str(Path(tempfile.gettempdir()) / "dreamos_test"),
            "memory": "memory",
            "templates": "templates"
        },
        "memory_check_interval": 1,  # 1 second for testing
        "max_retries": 3
    } 
