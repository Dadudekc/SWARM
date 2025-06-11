"""
Bridge Test Utilities
-------------------
Provides utilities for testing bridge functionality.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import pytest
from tests.utils.test_environment import TestEnvironment

class MockBridgeResponse:
    """Mock bridge response for testing."""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error: Optional[str] = None
    ):
        """Initialize mock response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            status: Response status
            error: Optional error message
        """
        self.content = content
        self.metadata = metadata or {}
        self.status = status
        self.error = error
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status,
            "error": self.error,
            "timestamp": self.timestamp
        }
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

class BridgeTestEnvironment:
    """Test environment for bridge testing."""
    
    def __init__(self, test_env):
        """Initialize bridge test environment.
        
        Args:
            test_env: TestEnvironment instance
        """
        self.test_env = test_env
        self.outbox_dir = test_env.get_test_dir("output") / "bridge_outbox"
        self.inbox_dir = test_env.get_test_dir("input") / "bridge_inbox"
        self.archive_dir = test_env.get_test_dir("archive") / "bridge_archive"
        self.failed_dir = test_env.get_test_dir("failed") / "bridge_failed"
        
        # Create directories
        for dir_path in [self.outbox_dir, self.inbox_dir, self.archive_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def create_test_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Create a test message file.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Path to created message file
        """
        message = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        file_path = self.outbox_dir / f"test_message_{datetime.now().timestamp()}.json"
        file_path.write_text(json.dumps(message, indent=2))
        return file_path
        
    def create_test_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error: Optional[str] = None
    ) -> Path:
        """Create a test response file.
        
        Args:
            content: Response content
            metadata: Optional metadata
            status: Response status
            error: Optional error message
            
        Returns:
            Path to created response file
        """
        response = MockBridgeResponse(content, metadata, status, error)
        
        file_path = self.inbox_dir / f"test_response_{datetime.now().timestamp()}.json"
        file_path.write_text(response.to_json())
        return file_path
        
    def get_messages(self) -> list[Dict[str, Any]]:
        """Get all messages in outbox.
        
        Returns:
            List of message dictionaries
        """
        messages = []
        for file_path in self.outbox_dir.glob("*.json"):
            with open(file_path) as f:
                messages.append(json.load(f))
        return messages
        
    def get_responses(self) -> list[Dict[str, Any]]:
        """Get all responses in inbox.
        
        Returns:
            List of response dictionaries
        """
        responses = []
        for file_path in self.inbox_dir.glob("*.json"):
            with open(file_path) as f:
                responses.append(json.load(f))
        return responses
        
    def clear_messages(self):
        """Clear all message files."""
        for file_path in self.outbox_dir.glob("*.json"):
            file_path.unlink()
            
    def clear_responses(self):
        """Clear all response files."""
        for file_path in self.inbox_dir.glob("*.json"):
            file_path.unlink()
            
    def cleanup(self):
        """Clean up test environment."""
        self.clear_messages()
        self.clear_responses()
        
        # Clean up archive and failed directories
        for dir_path in [self.archive_dir, self.failed_dir]:
            for file_path in dir_path.glob("*.json"):
                file_path.unlink()

class MockBridge:
    """Mock bridge for testing."""
    
    def __init__(self, test_env: BridgeTestEnvironment):
        """Initialize mock bridge.
        
        Args:
            test_env: BridgeTestEnvironment instance
        """
        self.test_env = test_env
        self.is_running = False
        self._response_queue = asyncio.Queue()
        
    async def start(self):
        """Start the bridge."""
        self.is_running = True
        
    async def stop(self):
        """Stop the bridge."""
        self.is_running = False
        
    async def send_message(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message through the bridge.
        
        Args:
            message: Message to send
            metadata: Optional metadata
            
        Returns:
            Response dictionary
        """
        if not self.is_running:
            raise RuntimeError("Bridge is not running")
            
        # Create test message
        self.test_env.create_test_message(message, metadata)
        
        # Wait for response
        try:
            response = await asyncio.wait_for(
                self._response_queue.get(),
                timeout=5.0
            )
            return response.to_dict()
        except asyncio.TimeoutError:
            return {
                "content": "",
                "status": "error",
                "error": "Timeout waiting for response",
                "timestamp": datetime.now().isoformat()
            }
            
    async def receive_message(
        self,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Receive a message from the bridge.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Message dictionary or None if timeout
        """
        if not self.is_running:
            raise RuntimeError("Bridge is not running")
            
        messages = self.test_env.get_messages()
        if not messages:
            return None
            
        return messages[0]
        
    async def validate_response(
        self,
        response: Dict[str, Any]
    ) -> bool:
        """Validate a response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        return (
            isinstance(response, dict) and
            "content" in response and
            "status" in response and
            "timestamp" in response
        )
        
    async def get_health(self) -> Dict[str, Any]:
        """Get bridge health status.
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.is_running else "stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics.
        
        Returns:
            Metrics dictionary
        """
        return {
            "messages_sent": len(self.test_env.get_messages()),
            "responses_received": len(self.test_env.get_responses()),
            "timestamp": datetime.now().isoformat()
        }
        
    async def queue_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error: Optional[str] = None
    ):
        """Queue a response for testing.
        
        Args:
            content: Response content
            metadata: Optional metadata
            status: Response status
            error: Optional error message
        """
        response = MockBridgeResponse(content, metadata, status, error)
        await self._response_queue.put(response)
        self.test_env.create_test_response(content, metadata, status, error)

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for bridge tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def bridge_dir(test_env: TestEnvironment) -> Path:
    """Get bridge test directory."""
    bridge_dir = test_env.get_test_dir("temp") / "bridge"
    bridge_dir.mkdir(exist_ok=True)
    return bridge_dir

@pytest.fixture
def outbox_dir(test_env: TestEnvironment) -> Path:
    """Get outbox test directory."""
    outbox_dir = test_env.get_test_dir("output") / "bridge_outbox"
    outbox_dir.mkdir(exist_ok=True)
    return outbox_dir

@pytest.fixture
def agent_dir(test_env: TestEnvironment) -> Path:
    """Get agent test directory."""
    agent_dir = test_env.get_test_dir("temp") / "agents"
    agent_dir.mkdir(exist_ok=True)
    return agent_dir

@pytest.fixture
def test_files(test_env: TestEnvironment) -> list[Path]:
    """Create test files for bridge tests."""
    files = []
    for i in range(3):
        file_path = test_env.get_test_dir("temp") / f"bridge_test_{i}.json"
        file_path.write_text(f'{{"id": {i}, "content": "test {i}"}}')
        files.append(file_path)
    return files 