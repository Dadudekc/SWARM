"""
Unified Handler Tests
------------------
Tests for the unified handler implementation.
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

from dreamos.core.handlers.unified_handler import UnifiedHandler
from dreamos.core.handlers.tests.test_handler import TestHandler

@pytest.mark.asyncio
async def test_handler_initialization(test_config):
    """Test handler initialization."""
    handler = TestHandler(config=test_config)
    assert handler.name == test_config["name"]
    assert handler.max_retries == test_config["max_retries"]
    assert handler.retry_delay == test_config["retry_delay"]

@pytest.mark.asyncio
async def test_handler_validation():
    """Test handler validation."""
    handler = TestHandler()
    
    # Test valid data
    assert await handler.validate("test") is True
    assert await handler.validate({"key": "value"}) is True
    
    # Test invalid data
    assert await handler.validate(123) is False
    assert await handler.validate(None) is False

@pytest.mark.asyncio
async def test_handler_processing():
    """Test handler processing."""
    handler = TestHandler()
    
    # Test string data
    result = await handler.handle("test_data")
    assert result["success"] is True
    assert "test_data" in result["processed_items"]
    
    # Test dict data
    result = await handler.handle({"key": "value"})
    assert result["success"] is True
    assert str({"key": "value"}) in result["processed_items"]
    
    # Test invalid data
    result = await handler.handle(123)
    assert result["success"] is False

@pytest.mark.asyncio
async def test_file_watching(test_dir):
    """Test file watching functionality."""
    handler = TestHandler()
    
    # Create test file
    test_file = test_dir / "test.json"
    with open(test_file, "w") as f:
        json.dump({"test": "data"}, f)
    
    # Watch file
    await handler.watch_file(
        test_file,
        handler.process_file,
        lambda e, p: handler.log_operation("error", str(e), ["watch", "error"])
    )
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify processing
    assert test_file.name in handler.processed_items

@pytest.mark.asyncio
async def test_json_operations(test_dir):
    """Test JSON operations."""
    handler = TestHandler()
    
    # Test file path
    test_file = test_dir / "test_config.json"
    
    # Test with default data
    success = await handler.process_json_file(
        test_file,
        lambda data: handler.handle(data),
        {"default": "data"}
    )
    assert success is True
    
    # Verify file contents
    with open(test_file) as f:
        data = json.load(f)
    assert data == {"default": "data"}

@pytest.mark.asyncio
async def test_retry_logic():
    """Test retry logic."""
    handler = TestHandler()
    
    # Test successful operation
    result = await handler.execute_with_retry(
        handler.handle,
        "test_data",
        success_message="Test passed",
        error_message="Test failed"
    )
    assert result["success"] is True
    assert "Test passed" in result["message"]
    
    # Test failed operation
    result = await handler.execute_with_retry(
        lambda x: 1/0,  # Force error
        "test_data",
        success_message="Test passed",
        error_message="Test failed"
    )
    assert result["success"] is False
    assert "Test failed" in result["message"]

@pytest.mark.asyncio
async def test_lifecycle():
    """Test handler lifecycle."""
    handler = TestHandler()
    
    # Test start
    await handler.start()
    assert handler._shutdown_event.is_set() is False
    
    # Test stop
    await handler.stop()
    assert handler._shutdown_event.is_set() is True
    assert len(handler._active_tasks) == 0 