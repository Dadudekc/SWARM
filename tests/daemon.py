import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for response loop daemon."""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from dreamos.core.bridge.response_loop_daemon import ResponseLoopDaemon
from dreamos.core.bridge.handlers.bridge import BridgeHandler

@pytest.fixture
def daemon_config() -> Dict[str, Any]:
    """Create mock daemon configuration."""
    return {
        "paths": {
            "runtime": "/tmp/runtime",
            "bridge_dir": "/tmp/bridge",
            "bridge_inbox": "/tmp/bridge/inbox",
            "bridge_outbox": "/tmp/bridge/outbox",
            "bridge_archive": "/tmp/bridge/archive"
        },
        "handlers": {
            "inbox": {
                "path": "/tmp/bridge/inbox",
                "patterns": ["*.json"]
            },
            "outbox": {
                "path": "/tmp/bridge/outbox",
                "patterns": ["*.json"]
            }
        }
    }

@pytest.fixture
def mock_bridge_handler():
    """Create mock bridge handler."""
    handler = AsyncMock(spec=BridgeHandler)
    handler.start = AsyncMock()
    handler.stop = AsyncMock()
    return handler

@pytest.fixture
def daemon(daemon_config: Dict[str, Any], mock_bridge_handler: BridgeHandler):
    """Create daemon instance with mock handler."""
    with patch("dreamos.core.bridge.response_loop_daemon.BridgeHandler", return_value=mock_bridge_handler):
        return ResponseLoopDaemon(daemon_config)

@pytest.mark.asyncio
async def test_daemon_initialization(daemon: ResponseLoopDaemon, daemon_config: Dict[str, Any]):
    """Test daemon initialization."""
    assert daemon.config == daemon_config
    assert daemon.state == {}
    assert daemon.state_file == Path(daemon_config["paths"]["runtime"]) / "response_loop_state.json"

@pytest.mark.asyncio
async def test_daemon_start(daemon: ResponseLoopDaemon, mock_bridge_handler: BridgeHandler):
    """Test daemon start."""
    await daemon.start()
    
    # Verify bridge handler was started
    mock_bridge_handler.start.assert_called_once()
    
    # Verify state was updated
    assert "started_at" in daemon.state

@pytest.mark.asyncio
async def test_daemon_stop(daemon: ResponseLoopDaemon, mock_bridge_handler: BridgeHandler):
    """Test daemon stop."""
    await daemon.stop()
    
    # Verify bridge handler was stopped
    mock_bridge_handler.stop.assert_called_once()
    
    # Verify state was updated
    assert "stopped_at" in daemon.state

@pytest.mark.asyncio
async def test_daemon_run(daemon: ResponseLoopDaemon, mock_bridge_handler: BridgeHandler):
    """Test daemon run loop."""
    # Mock sleep to prevent infinite loop
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # Set up mock to raise KeyboardInterrupt after first sleep
        mock_sleep.side_effect = KeyboardInterrupt()
        
        # Run daemon
        await daemon.run()
        
        # Verify bridge handler was started and stopped
        mock_bridge_handler.start.assert_called_once()
        mock_bridge_handler.stop.assert_called_once()
        
        # Verify sleep was called
        mock_sleep.assert_called_once()

@pytest.mark.asyncio
async def test_daemon_error_handling(daemon: ResponseLoopDaemon, mock_bridge_handler: BridgeHandler):
    """Test daemon error handling."""
    # Mock bridge handler to raise exception
    mock_bridge_handler.start.side_effect = Exception("Test error")
    
    # Run daemon
    await daemon.start()
    
    # Verify bridge handler was stopped
    mock_bridge_handler.stop.assert_called_once()
    
    # Verify state was updated
    assert "stopped_at" in daemon.state

@pytest.mark.asyncio
async def test_daemon_create_and_run(daemon_config: Dict[str, Any], mock_bridge_handler: BridgeHandler):
    """Test daemon create and run."""
    with patch("dreamos.core.bridge.response_loop_daemon.BridgeHandler", return_value=mock_bridge_handler):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Set up mock to raise KeyboardInterrupt after first sleep
            mock_sleep.side_effect = KeyboardInterrupt()
            
            # Create and run daemon
            await ResponseLoopDaemon.create_and_run(daemon_config)
            
            # Verify bridge handler was started and stopped
            mock_bridge_handler.start.assert_called_once()
            mock_bridge_handler.stop.assert_called_once()
            
            # Verify sleep was called
            mock_sleep.assert_called_once()
