"""
Tests for Response Handler implementation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from dreamos.core.bridge.chatgpt.response_handler import ChatGPTResponseHandler
from tests.utils.bridge_test_utils import BridgeTestEnvironment, MockBridge

@pytest.fixture
def bridge_env(test_env):
    """Create bridge test environment."""
    env = BridgeTestEnvironment(test_env)
    yield env
    env.cleanup()

@pytest.fixture
def mock_bridge(bridge_env):
    """Create mock bridge."""
    bridge = MockBridge(bridge_env)
    return bridge

@pytest.fixture
def response_handler(bridge_env, mock_bridge):
    """Create response handler instance."""
    config = {
        "paths": {
            "output": str(bridge_env.outbox_dir),
            "archive": str(bridge_env.archive_dir)
        },
        "test_mode": True
    }
    handler = ChatGPTResponseHandler(config, bridge=mock_bridge)
    return handler

def test_extract_reply(response_handler):
    """Test extract_reply functionality."""
    # Test valid response
    response = {
        "content": "Here's the code:\n```python\nprint('Hello')\n```",
        "metadata": {"test": True}
    }
    reply = response_handler.extract_reply(response)
    assert reply == "print('Hello')"
    
    # Test response without code block
    response = {
        "content": "This is a regular response",
        "metadata": {"test": True}
    }
    reply = response_handler.extract_reply(response)
    assert reply == "This is a regular response"
    
    # Test response with multiple code blocks
    response = {
        "content": "First block:\n```python\nprint('First')\n```\nSecond block:\n```python\nprint('Second')\n```",
        "metadata": {"test": True}
    }
    reply = response_handler.extract_reply(response)
    assert reply == "print('First')\nprint('Second')"
    
    # Test response with non-Python code block
    response = {
        "content": "Here's the code:\n```javascript\nconsole.log('Hello')\n```",
        "metadata": {"test": True}
    }
    reply = response_handler.extract_reply(response)
    assert reply == "console.log('Hello')"

def test_parse_output(response_handler):
    """Test parse_output functionality."""
    # Test valid output
    output = "```python\nprint('Hello')\n```"
    parsed = response_handler.parse_output(output)
    assert parsed == "print('Hello')"
    
    # Test output without code block
    output = "This is a regular output"
    parsed = response_handler.parse_output(output)
    assert parsed == output
    
    # Test output with multiple code blocks
    output = "```python\nprint('First')\n```\n```python\nprint('Second')\n```"
    parsed = response_handler.parse_output(output)
    assert parsed == "print('First')\nprint('Second')"
    
    # Test output with non-Python code block
    output = "```javascript\nconsole.log('Hello')\n```"
    parsed = response_handler.parse_output(output)
    assert parsed == "console.log('Hello')"

@pytest.mark.asyncio
async def test_process_response(response_handler, bridge_env):
    """Test process_response functionality."""
    # Create test response
    response = {
        "content": "Here's the code:\n```python\nprint('Hello')\n```",
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat()
    }
    
    # Process response
    result = await response_handler.process_response(response)
    
    # Verify result
    assert result is not None
    assert result["content"] == "print('Hello')"
    assert result["metadata"]["test"] is True
    
    # Verify response was saved
    responses = bridge_env.get_responses()
    assert len(responses) == 1
    assert responses[0]["content"] == "print('Hello')"

@pytest.mark.asyncio
async def test_error_handling(response_handler, bridge_env):
    """Test error handling functionality."""
    # Test invalid response
    with pytest.raises(ValueError):
        await response_handler.process_response(None)
    
    # Test response with invalid content
    response = {
        "content": None,
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat()
    }
    result = await response_handler.process_response(response)
    assert result["status"] == "error"
    assert "Invalid content" in result["error"]
    
    # Test response with missing required fields
    response = {
        "content": "Test content"
        # Missing metadata and timestamp
    }
    result = await response_handler.process_response(response)
    assert result["status"] == "error"
    assert "Missing required fields" in result["error"]

@pytest.mark.asyncio
async def test_response_validation(response_handler, bridge_env):
    """Test response validation."""
    # Test valid response
    response = {
        "content": "Here's the code:\n```python\nprint('Hello')\n```",
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat()
    }
    is_valid = await response_handler.validate_response(response)
    assert is_valid
    
    # Test response with empty content
    response = {
        "content": "",
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat()
    }
    is_valid = await response_handler.validate_response(response)
    assert not is_valid
    
    # Test response with invalid metadata
    response = {
        "content": "Test content",
        "metadata": "invalid",  # Should be dict
        "timestamp": datetime.now().isoformat()
    }
    is_valid = await response_handler.validate_response(response)
    assert not is_valid
    
    # Test response with invalid timestamp
    response = {
        "content": "Test content",
        "metadata": {"test": True},
        "timestamp": "invalid"  # Should be ISO format
    }
    is_valid = await response_handler.validate_response(response)
    assert not is_valid

@pytest.mark.asyncio
async def test_response_archiving(response_handler, bridge_env):
    """Test response archiving functionality."""
    # Create test response
    response = {
        "content": "Here's the code:\n```python\nprint('Hello')\n```",
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat()
    }
    
    # Process response
    await response_handler.process_response(response)
    
    # Verify response was archived
    archive_files = list(bridge_env.archive_dir.glob("*.json"))
    assert len(archive_files) == 1
    
    # Verify archive content
    with open(archive_files[0]) as f:
        archived = json.load(f)
        assert archived["content"] == "print('Hello')"
        assert archived["metadata"]["test"] is True
        assert "timestamp" in archived

@pytest.mark.asyncio
async def test_response_retry(response_handler, bridge_env, mock_bridge):
    """Test response retry functionality."""
    # Create test response with error
    response = {
        "content": "Here's the code:\n```python\nprint('Hello')\n```",
        "metadata": {"test": True},
        "timestamp": datetime.now().isoformat(),
        "status": "error",
        "error": "Test error"
    }
    
    # Process response with retry
    result = await response_handler.process_response(response, retry=True)
    
    # Verify retry was attempted
    assert result["status"] == "success"
    assert result["content"] == "print('Hello')"
    
    # Verify response was archived
    archive_files = list(bridge_env.archive_dir.glob("*.json"))
    assert len(archive_files) == 1
    
    # Verify archive content
    with open(archive_files[0]) as f:
        archived = json.load(f)
        assert archived["content"] == "print('Hello')"
        assert archived["metadata"]["test"] is True
        assert archived["status"] == "success" 