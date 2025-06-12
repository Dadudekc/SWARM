"""Tests for agent_bridge_handler module."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path
from dreamos.core.messaging.agent_bridge_handler import AgentBridgeHandler

# Fixtures
@pytest.fixture
def mock_bridge_integration():
    """Create a mock bridge integration."""
    mock = Mock()
    mock.get_bridge_status.return_value = {
        "handler_running": True,
        "last_response": "test response"
    }
    return mock

@pytest.fixture
def mock_response_tracker():
    """Create a mock response tracker."""
    mock = Mock()
    mock.get_response_history.return_value = [
        {"content": "test response", "timestamp": "2024-01-01T00:00:00"}
    ]
    return mock

@pytest.fixture
def bridge_handler(mock_bridge_integration, mock_response_tracker):
    """Create a bridge handler instance with mocked dependencies."""
    with patch('dreamos.core.messaging.agent_bridge_handler.BridgeIntegration', return_value=mock_bridge_integration), \
         patch('dreamos.core.messaging.agent_bridge_handler.AgentResponseTracker', return_value=mock_response_tracker):
        handler = AgentBridgeHandler(config={"bridge_outbox_dir": "test_outbox"})
        return handler

@pytest.mark.asyncio
async def test_initialization(bridge_handler):
    """Test bridge handler initialization."""
    assert bridge_handler is not None
    assert hasattr(bridge_handler, 'handle_agent_message')
    assert hasattr(bridge_handler, 'get_agent_status')
    
    # Test initialize
    result = await bridge_handler.initialize()
    assert result is True
    assert Path("test_outbox").exists()

@pytest.mark.asyncio
async def test_handle_agent_message(bridge_handler):
    """Test message handling."""
    result = await bridge_handler.handle_agent_message(
        agent_id="test-agent",
        message="test message"
    )
    assert result is True
    assert Path("test_outbox/agent-test-agent.json").exists()

@pytest.mark.asyncio
async def test_get_agent_status(bridge_handler):
    """Test getting agent status."""
    status = await bridge_handler.get_agent_status("test-agent")
    assert isinstance(status, dict)
    assert status["bridge"]["handler_running"] is True
    assert len(status["recent_responses"]) == 1
    assert status["recent_responses"][0]["content"] == "test response" 