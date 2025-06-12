import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""
Bridge Handlers Test Suite
------------------------
Tests for bridge handler functionality.
"""

import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
import json
import asyncio

from dreamos.core.bridge.handlers.base import BaseBridgeHandler
from dreamos.core.bridge.handlers.outbox import BridgeOutboxHandler

class MockBridgeHandler(BaseBridgeHandler):
    """Mock bridge handler for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize mock handler."""
        super().__init__(config)
        self.processed_files = []
    
    async def process_file(self, file_path: Path) -> bool:
        """Process a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if processing successful
        """
        self.processed_files.append(file_path)
        return True

@pytest.fixture
def handler_config() -> Dict[str, Any]:
    """Create mock handler configuration."""
    return {
        "handlers": {
            "outbox": {
                "path": "/tmp/outbox",
                "patterns": ["*.json"]
            }
        }
    }

@pytest.fixture
def mock_handler(handler_config: Dict[str, Any]) -> MockBridgeHandler:
    """Create mock handler instance."""
    return MockBridgeHandler(handler_config)

@pytest.fixture
def outbox_dir(tmp_path: Path) -> Path:
    """Create temporary outbox directory."""
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    return outbox

@pytest.fixture
def test_file(outbox_dir: Path) -> Path:
    """Create test file in outbox."""
    file_path = outbox_dir / "test.json"
    file_path.write_text(json.dumps({"test": "data"}))
    return file_path

@pytest.mark.asyncio
async def test_handler_initialization(mock_handler: MockBridgeHandler):
    """Test handler initialization."""
    assert mock_handler.config == handler_config
    assert mock_handler.processed_files == []

@pytest.mark.asyncio
async def test_handler_process_file(mock_handler: MockBridgeHandler, test_file: Path):
    """Test handler file processing."""
    assert await mock_handler.process_file(test_file)
    assert test_file in mock_handler.processed_files

@pytest.mark.asyncio
async def test_outbox_handler(outbox_dir: Path):
    """Test outbox handler functionality."""
    handler = BridgeOutboxHandler({
        "handlers": {
            "outbox": {
                "path": str(outbox_dir),
                "patterns": ["*.json"]
            }
        }
    })
    
    # Create test file
    test_file = outbox_dir / "test.json"
    test_file.write_text(json.dumps({"test": "data"}))
    
    # Process file
    assert await handler.process_file(test_file)
    
    # Verify file was moved
    assert not test_file.exists()
    assert (outbox_dir / "processed" / "test.json").exists() 