"""Integration tests for ChatGPT bridge with CellPhone messaging system."""

import pytest
import asyncio
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.chatgpt_bridge import ChatGPTBridge

# Swarm test markers
pytestmark = [
    pytest.mark.swarm_core,
    pytest.mark.bridge_integration,
    pytest.mark.cellphone_pipeline
]

# Test metadata for Codex validation
TEST_METADATA = {
    "component": "chatgpt_bridge",
    "critical_path": True,
    "dependencies": ["cell_phone", "undetected_chromedriver"],
    "failure_impact": "high",
    "recovery_strategy": "retry_with_backoff"
}

def pytest_collection_modifyitems(items):
    """Add test metadata to each test item."""
    for item in items:
        item.user_properties.append(("metadata", TEST_METADATA))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup and teardown test environment."""
    # Create test artifacts directory
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup after tests
    if artifacts_dir.exists():
        for file in artifacts_dir.glob("*"):
            file.unlink()

@pytest.fixture
def cell_phone(monkeypatch):
    """Get fresh CellPhone instance with async-compatible send_message."""
    CellPhone.reset_singleton()
    phone = CellPhone()
    # Patch send_message with an async-compatible mock
    monkeypatch.setattr(phone, "send_message", AsyncMock(return_value=True))
    return phone

@pytest.fixture
def bridge():
    """Get ChatGPT bridge instance with mocked browser."""
    with patch('undetected_chromedriver.Chrome') as mock_chrome:
        bridge = ChatGPTBridge()
        bridge.driver = Mock()
        yield bridge

@pytest.mark.asyncio
async def test_basic_message_flow(cell_phone, bridge):
    """Test basic message flow from agent to ChatGPT and back."""
    # Setup mock response
    bridge.driver.find_elements.return_value = [
        Mock(text="Test response from ChatGPT")
    ]
    
    # Send message through bridge
    await bridge.request_chatgpt_response(
        agent_id="Agent-Test",
        prompt="Test prompt"
    )
    
    # Process the queue using the new method
    await bridge.process_pending()
    
    # Check message was received
    status = cell_phone.get_message_status("Agent-Test")
    assert status is not None
    assert len(status["message_history"]) > 0
    assert "Test response from ChatGPT" in status["message_history"][-1]["content"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "basic_flow.json", "w") as f:
        json.dump({
            "request": {
                "agent_id": "Agent-Test",
                "prompt": "Test prompt"
            },
            "response": status["message_history"][-1]["content"],
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_error_handling(cell_phone, bridge):
    """Test error handling and retry logic."""
    # Setup mock to fail twice then succeed
    bridge.driver.find_elements.side_effect = [
        Exception("First failure"),
        Exception("Second failure"),
        [Mock(text="Success after retries")]
    ]
    
    # Send message
    await bridge.request_chatgpt_response(
        agent_id="Agent-Test",
        prompt="Test prompt"
    )
    
    # Process the queue using the new method
    await bridge.process_pending()
    
    # Check final status
    status = cell_phone.get_message_status("Agent-Test")
    assert status is not None
    assert "Success after retries" in status["message_history"][-1]["content"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "error_handling.json", "w") as f:
        json.dump({
            "failures": [
                {"attempt": 1, "error": "First failure"},
                {"attempt": 2, "error": "Second failure"}
            ],
            "final_response": status["message_history"][-1]["content"],
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_queue_management(cell_phone, bridge):
    """Test message queue management under load."""
    # Setup mock response
    bridge.driver.find_elements.return_value = [
        Mock(text=f"Response {i}") for i in range(5)
    ]
    
    # Send multiple messages
    for i in range(5):
        await bridge.request_chatgpt_response(
            agent_id="Agent-Test",
            prompt=f"Test prompt {i}"
        )
    
    # Process all messages at once
    await bridge.process_pending()
    
    # Check queue state
    status = cell_phone.get_message_status("Agent-Test")
    assert status is not None
    assert len(status["message_history"]) == 5
    
    # Verify message order
    for i, msg in enumerate(status["message_history"]):
        assert f"Response {i}" in msg["content"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "queue_management.json", "w") as f:
        json.dump({
            "message_count": len(status["message_history"]),
            "responses": [msg["content"] for msg in status["message_history"]],
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_invalid_agent_handling(cell_phone, bridge):
    """Test handling of invalid agent IDs."""
    # Try to send to invalid agent
    with pytest.raises(ValueError):
        await bridge.request_chatgpt_response(
            agent_id="invalid-agent",
            prompt="Test prompt"
        )
    
    # Verify no messages sent
    status = cell_phone.get_message_status("invalid-agent")
    assert status is not None
    assert len(status["message_history"]) == 0
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "invalid_agent.json", "w") as f:
        json.dump({
            "invalid_agent_id": "invalid-agent",
            "error": "ValueError",
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_bridge_health_check(cell_phone, bridge):
    """Test bridge health monitoring."""
    # Check initial health
    bridge._update_health(True)
    
    # Simulate error
    bridge._update_health(False, "Test error")
    
    # Verify health file
    health_data = bridge._load_health()
    assert not health_data["ready"]
    assert "Test error" in health_data["error"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "health_check.json", "w") as f:
        json.dump({
            "initial_health": True,
            "error_health": health_data,
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_concurrent_requests(cell_phone, bridge):
    """Test handling of concurrent requests."""
    # Setup mock to handle concurrent requests
    responses = [f"Response {i}" for i in range(3)]
    bridge.driver.find_elements.side_effect = [
        [Mock(text=resp)] for resp in responses
    ]
    
    # Send concurrent requests
    tasks = []
    for i in range(3):
        tasks.append(
            bridge.request_chatgpt_response(
                agent_id=f"Agent-Test-{i}",
                prompt=f"Test prompt {i}"
            )
        )
    
    # Wait for all to complete
    await asyncio.gather(*tasks)
    
    # Process all queued messages using the new method
    await bridge.process_pending()
    
    # Verify all messages processed
    for i in range(3):
        status = cell_phone.get_message_status(f"Agent-Test-{i}")
        assert status is not None
        assert f"Response {i}" in status["message_history"][-1]["content"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "concurrent_requests.json", "w") as f:
        json.dump({
            "concurrent_count": 3,
            "responses": [
                {
                    "agent_id": f"Agent-Test-{i}",
                    "response": status["message_history"][-1]["content"]
                }
                for i in range(3)
            ],
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_bridge_shutdown(cell_phone, bridge):
    """Test graceful bridge shutdown."""
    # Start bridge
    bridge.start()
    
    # Send a message
    await bridge.request_chatgpt_response(
        agent_id="Agent-Test",
        prompt="Test prompt"
    )
    
    # Process the message using the new method
    await bridge.process_pending()
    
    # Shutdown
    bridge.stop()
    
    # Verify shutdown
    assert not bridge.is_running
    assert bridge.worker_thread is None or not bridge.worker_thread.is_alive()
    
    # Verify health status
    health_data = bridge._load_health()
    assert not health_data["ready"]
    assert "Bridge stopped" in health_data["error"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "shutdown.json", "w") as f:
        json.dump({
            "shutdown_state": {
                "is_running": bridge.is_running,
                "worker_thread_alive": bridge.worker_thread.is_alive() if bridge.worker_thread else False,
                "health_status": health_data
            },
            "timestamp": time.time()
        }, f, indent=2)

@pytest.mark.asyncio
async def test_process_pending_handles_empty_queue(bridge):
    """Test that process_pending handles empty queue gracefully."""
    # Should not raise any error
    await bridge.process_pending()
    assert bridge.pending_queue.empty()
    
    # Verify health status remains valid
    health_data = bridge._load_health()
    assert health_data["ready"]
    
    # Log test artifacts for Codex validation
    artifacts_dir = Path("test_artifacts/chatgpt_bridge")
    with open(artifacts_dir / "empty_queue.json", "w") as f:
        json.dump({
            "queue_empty": bridge.pending_queue.empty(),
            "health_status": health_data,
            "timestamp": time.time()
        }, f, indent=2) 