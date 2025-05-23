"""
Test configuration for Discord bot tests.
"""

import os
import json
import yaml
from pathlib import Path

# Test directories
TEST_DATA_DIR = Path("tests/data")
TEST_CONFIG_DIR = Path("tests/test_config")

# Mock data
MOCK_AGENT_CONFIG = {
    "Agent-1": {
        "channel_id": 123456789,
        "role_id": 987654321
    },
    "Agent-2": {
        "channel_id": 234567890,
        "role_id": 876543210
    }
}

MOCK_PROMPT = {
    "prompt": "Test prompt",
    "context": "Test context",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 100
    }
}

MOCK_DEVLOG = """# Agent-1 Development Log

## 2024-03-20
- Initial test entry
- Added test functionality

## 2024-03-21
- Updated test cases
- Fixed bugs
"""

def setup_test_environment():
    """Set up the test environment."""
    try:
        # Create test directories
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        TEST_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        with open(TEST_CONFIG_DIR / "agent_config.yaml", "w") as f:
            yaml.dump(MOCK_AGENT_CONFIG, f)
        
        with open(TEST_DATA_DIR / "test_prompt.json", "w") as f:
            json.dump(MOCK_PROMPT, f)
        
        with open(TEST_DATA_DIR / "agent1_devlog.md", "w") as f:
            f.write(MOCK_DEVLOG)
    except Exception as e:
        print(f"Warning: Error setting up test environment: {e}")

def cleanup_test_environment():
    """Clean up the test environment."""
    try:
        # Remove test files
        if TEST_DATA_DIR.exists():
            for file in TEST_DATA_DIR.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Warning: Error removing file {file}: {e}")
            
            try:
                TEST_DATA_DIR.rmdir()
            except Exception as e:
                print(f"Warning: Error removing directory {TEST_DATA_DIR}: {e}")
        
        if TEST_CONFIG_DIR.exists():
            for file in TEST_CONFIG_DIR.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Warning: Error removing file {file}: {e}")
            
            try:
                TEST_CONFIG_DIR.rmdir()
            except Exception as e:
                print(f"Warning: Error removing directory {TEST_CONFIG_DIR}: {e}")
    except Exception as e:
        print(f"Warning: Error cleaning up test environment: {e}")

# Test bot settings
TEST_BOT_TOKEN = "test_token_123"
TEST_GUILD_ID = 123456789
TEST_CHANNEL_ID = 987654321

# Test user settings
TEST_USER_ID = 111222333
TEST_USER_NAME = "TestUser"

# Test message settings
TEST_MESSAGE_ID = 444555666
TEST_MESSAGE_CONTENT = "!help" 