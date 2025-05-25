import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session")
def temp_config_dir(tmp_path_factory):
    """Create a temporary directory for configuration files."""
    return tmp_path_factory.mktemp("config")

@pytest.fixture(scope="session")
def temp_log_dir(tmp_path_factory):
    """Create a temporary directory for log files."""
    return tmp_path_factory.mktemp("logs")

# The test runner now relies on pytest's discovery mechanism
# Individual test files should be named test_*.py and contain test_* functions
# pytest will automatically discover and run them

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 