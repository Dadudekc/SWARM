from pathlib import Path
import shutil
import logging
import os

TEST_ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"

MOCK_AGENT_CONFIG = {
    "name": "test_agent",
    "type": "test",
    "capabilities": ["test"],
    "settings": {
        "test_setting": "test_value"
    }
}

MOCK_PROMPT = "This is a test prompt for unit testing purposes."

MOCK_DEVLOG = {
    "title": "Test Devlog",
    "content": "This is a test devlog entry",
    "author": "test_user",
    "tags": ["test", "unit"],
    "metadata": {
        "version": "1.0.0",
        "type": "test"
    }
}


def safe_remove(path: Path) -> bool:
    """Remove a file or directory, ignoring errors."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def ensure_test_dirs() -> None:
    """Ensure all common test directories exist."""
    for d in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR,
              TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def setup_test_environment() -> None:
    """Set up the test environment.
    
    This function:
    1. Ensures all test directories exist
    2. Cleans up any existing test data
    3. Sets up logging
    4. Sets environment variables
    """
    # Clean up existing test data
    for d in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR,
              TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        safe_remove(d)
    
    # Create fresh test directories
    ensure_test_dirs()
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set environment variables
    os.environ['DREAMOS_TEST_MODE'] = '1'
    os.environ['DREAMOS_TEST_ROOT'] = str(TEST_ROOT)
    os.environ['DREAMOS_TEST_DATA_DIR'] = str(TEST_DATA_DIR)
    os.environ['DREAMOS_TEST_OUTPUT_DIR'] = str(TEST_OUTPUT_DIR)
    os.environ['DREAMOS_TEST_CONFIG_DIR'] = str(TEST_CONFIG_DIR)
    os.environ['DREAMOS_TEST_RUNTIME_DIR'] = str(TEST_RUNTIME_DIR)
    os.environ['DREAMOS_TEST_TEMP_DIR'] = str(TEST_TEMP_DIR)


def cleanup_test_environment() -> None:
    """Clean up the test environment.
    
    This function:
    1. Removes all test directories and their contents
    2. Clears test-related environment variables
    """
    # Remove test directories
    for d in [TEST_DATA_DIR, TEST_OUTPUT_DIR, VOICE_QUEUE_DIR, TEST_CONFIG_DIR,
              TEST_RUNTIME_DIR, TEST_TEMP_DIR]:
        safe_remove(d)
    
    # Clear environment variables
    for var in ['DREAMOS_TEST_MODE', 'DREAMOS_TEST_ROOT', 'DREAMOS_TEST_DATA_DIR',
                'DREAMOS_TEST_OUTPUT_DIR', 'DREAMOS_TEST_CONFIG_DIR',
                'DREAMOS_TEST_RUNTIME_DIR', 'DREAMOS_TEST_TEMP_DIR']:
        os.environ.pop(var, None)
