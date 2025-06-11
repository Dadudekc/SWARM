import pytest
import os
from pathlib import Path

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["DREAMOS_TEST_MODE"] = "1"
    os.environ["DREAMOS_LOG_LEVEL"] = "DEBUG"
    
    # Create test directories
    test_dirs = [
        "runtime/agent_memory/test_agent",
        "runtime/cache",
        "logs"
    ]
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup
    for dir_path in test_dirs:
        if Path(dir_path).exists():
            for file in Path(dir_path).glob("*"):
                if file.is_file():
                    file.unlink() 