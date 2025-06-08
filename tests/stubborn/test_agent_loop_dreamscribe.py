"""
Test suite for Dreamscribe integration in agent_loop.
"""

import pytest
import time
import json
from pathlib import Path
from dreamos.core.autonomy.agent_loop import AgentLoop
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.ai.dreamscribe import Dreamscribe
from dreamos.social.utils.log_manager import LogManager, LogConfig, LogLevel
from dreamos.core.messaging.message import Message
import os
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from typing import Dict, Any
import sys
import unittest

# Skip GUI tests if PyQt5 is not available
try:
    from PyQt5.QtWidgets import QWidget, QApplication
except ImportError:
    pytest.skip("PyQt5 not available - skipping GUI tests", allow_module_level=True)

if os.name == "nt" and "PyQt5" not in sys.modules:
    pytest.skip("GUI tests skipped – PyQt5 wheel missing on CI", allow_module_level=True)

skip_if_gui_disabled = pytest.mark.skipif(
    os.getenv("DISABLE_GUI_TESTS", "0") == "1",
    reason="GUI tests are disabled in this environment"
)

pytestmark = skip_if_gui_disabled

# Mock PyQt5 imports
import sys
from unittest.mock import MagicMock

class MockQtWidgets:
    class QMainWindow: pass
    class QWidget: pass
    class QVBoxLayout: pass
    class QPushButton: pass
    class QLabel: pass
    class QFrame: pass
    class QSizePolicy: pass

class MockQtCore:
    class Qt: pass
    class QSize: pass
    class QObject: pass
    class pyqtSignal: pass

class MockQtGui:
    class QFont: pass
    class QColor: pass
    class QPalette: pass

sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtWidgets'] = MockQtWidgets
sys.modules['PyQt5.QtCore'] = MockQtCore
sys.modules['PyQt5.QtGui'] = MockQtGui

pytestmark = pytest.mark.pyqt5

@pytest.fixture
def mock_agent_control():
    """Create a mock agent control instance."""
    with patch('dreamos.core.agent_control.AgentControl') as mock:
        control = mock.return_value
        control.move_to_agent = AsyncMock(return_value=True)
        control.click_input_box = AsyncMock(return_value=True)
        control.click_copy_button = AsyncMock(return_value=True)
        control.send_message = AsyncMock(return_value=True)
        yield control

@pytest.fixture
def agent_loop(mock_agent_control):
    """Create an agent loop instance."""
    return AgentLoop(mock_agent_control)

@pytest.fixture
def agent_loop():
    """Create a fresh AgentLoop instance for testing."""
    # Clear any existing test data
    test_paths = [
        Path("runtime/memory_corpus.json"),
        Path("runtime/insight_patterns.json"),
        Path("runtime/narrative_threads"),
        Path("runtime/agent_memory/test_agent/inbox.json")
    ]
    
    for path in test_paths:
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                for file in path.glob("*"):
                    file.unlink()
                path.rmdir()
    
    # Create test inbox
    inbox_path = Path("runtime/agent_memory/test_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    
    # Create test message
    test_message = {
        "id": "test_msg_1",
        "content": "Testing memory logging",
        "task_id": "TASK-001",
        "timestamp": time.time()
    }
    
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([test_message], f)
    
    # Create controller and loop
    controller = AgentController()
    return AgentLoop(controller)

@pytest.mark.asyncio
async def test_dreamscribe_content_logging(agent_loop):
    """Test that content is properly logged to Dreamscribe."""
    # Create test message
    message = {
        "id": "test_msg_1",
        "content": "Testing memory logging",
        "type": "agent_message",
        "priority": "NORMAL",
        "task_id": "TASK-001",
        "timestamp": time.time()
    }
    
    # Write message to inbox
    inbox_path = Path("runtime/agent_memory/test_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([message], f)
    
    # Process test agent's inbox
    await agent_loop._process_inbox("test_agent")
    
    # Verify memory was created
    dreamscribe = agent_loop.dreamscribe
    insights = dreamscribe.get_system_insights()
    
    # Check for content generation memory
    content_memories = []
    for thread_id in insights["narratives"]:
        memory_ids = dreamscribe.get_thread(thread_id)
        if not memory_ids:
            continue
            
        for memory_id in memory_ids:
            memory = dreamscribe.get_memory(memory_id)
            if (memory and 
                memory["context"].get("type") == "content_generated" and
                memory["context"].get("message_id") == "test_agent:test_msg_1"):
                content_memories.append(memory)
    
    assert len(content_memories) == 1
    assert content_memories[0]["content"] == "Testing memory logging"
    assert content_memories[0]["context"]["task_id"] == "TASK-001"

@pytest.mark.asyncio
async def test_dreamscribe_error_logging(agent_loop):
    """Test that errors are properly logged to Dreamscribe."""
    # Create invalid message
    inbox_path = Path("runtime/agent_memory/test_agent")
    invalid_message = {
        "id": "test_msg_2",
        "content": None,  # Invalid content
        "type": "agent_message",
        "priority": "NORMAL",
        "task_id": "TASK-002",
        "timestamp": time.time()
    }
    
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([invalid_message], f)
    
    # Process test agent's inbox
    await agent_loop._process_inbox("test_agent")
    
    # Verify error was logged
    dreamscribe = agent_loop.dreamscribe
    insights = dreamscribe.get_system_insights()
    
    # Check for error memory
    error_memories = []
    for thread_id in insights["narratives"]:
        memory_ids = dreamscribe.get_thread(thread_id)
        if not memory_ids:
            continue
            
        for memory_id in memory_ids:
            memory = dreamscribe.get_memory(memory_id)
            if (memory and 
                memory["context"].get("type") == "task_completed" and
                memory["context"].get("status") == "error" and
                memory["context"].get("message_id") == "test_agent:test_msg_2"):
                error_memories.append(memory)
    
    assert len(error_memories) == 1
    assert error_memories[0]["context"]["task_id"] == "TASK-002"

@pytest.mark.asyncio
async def test_agent_loop_initialization(agent_loop):
    """Test agent loop initialization."""
    assert agent_loop.controller is not None
    assert agent_loop.dreamscribe is not None
    assert agent_loop.log_manager is not None

@pytest.mark.asyncio
async def test_agent_loop_message_processing(agent_loop):
    """Test message processing in agent loop."""
    # Create test message
    message = {
        "id": "test_msg_1",
        "content": "Test message",
        "type": "text",
        "priority": "NORMAL",
        "task_id": "TASK-001",
        "timestamp": time.time()
    }
    
    # Write message to inbox
    inbox_path = Path("runtime/agent_memory/test_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([message], f)
    
    # Process message
    await agent_loop._process_inbox("test_agent")
    
    # Verify message was processed
    assert agent_loop.controller.message_processor.get_queue_size() == 0

@pytest.mark.asyncio
async def test_agent_loop_error_handling(agent_loop):
    """Test error handling in agent loop."""
    # Create test message with invalid content
    message = {
        "id": "test_msg_2",
        "content": None,  # Invalid content
        "type": "text",
        "priority": "NORMAL",
        "task_id": "TASK-002",
        "timestamp": time.time()
    }
    
    # Write message to inbox
    inbox_path = Path("runtime/agent_memory/test_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([message], f)
    
    # Process message
    await agent_loop._process_inbox("test_agent")
    
    # Verify error was logged
    assert agent_loop.controller.message_processor.get_queue_size() == 0

@pytest.mark.asyncio
async def test_agent_loop_invalid_agent(agent_loop):
    """Test handling of invalid agent."""
    # Create test message
    message = {
        "id": "test_msg_3",
        "content": "Test message",
        "type": "text",
        "priority": "NORMAL",
        "task_id": "TASK-003",
        "timestamp": time.time()
    }
    
    # Write message to inbox
    inbox_path = Path("runtime/agent_memory/invalid_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([message], f)
    
    # Process message for invalid agent
    await agent_loop._process_inbox("invalid_agent")
    
    # Verify no errors occurred
    assert agent_loop.controller.message_processor.get_queue_size() == 0

@pytest.mark.asyncio
async def test_dreamscribe_response_logging(agent_loop, monkeypatch):
    """Test that responses are properly logged to Dreamscribe."""
    # Mock message processor response
    async def mock_send_message(message: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "content": "Test response",
            "status": "success",
            "timestamp": time.time()
        }
    
    monkeypatch.setattr(
        agent_loop.controller.message_processor,
        "send_message",
        mock_send_message
    )
    
    # Create test message
    inbox_path = Path("runtime/agent_memory/test_agent")
    inbox_path.mkdir(parents=True, exist_ok=True)
    test_message = {
        "id": "test_msg_3",
        "content": "Testing response logging",
        "type": "agent_message",
        "priority": "NORMAL",
        "task_id": "TASK-003",
        "timestamp": time.time()
    }
    
    with open(inbox_path / "inbox.json", "w") as f:
        json.dump([test_message], f)
    
    # Process test agent's inbox
    await agent_loop._process_inbox("test_agent")
    
    # Verify memory was created
    dreamscribe = agent_loop.dreamscribe
    insights = dreamscribe.get_system_insights()
    
    # Check for response memory
    response_memories = []
    for thread_id in insights["narratives"]:
        memory_ids = dreamscribe.get_thread(thread_id)
        if not memory_ids:
            continue
            
        for memory_id in memory_ids:
            memory = dreamscribe.get_memory(memory_id)
            if (memory and 
                memory["context"].get("type") == "response" and
                memory["context"].get("message_id") == "test_agent:test_msg_3"):
                response_memories.append(memory)
    
    assert len(response_memories) == 1
    assert response_memories[0]["context"]["task_id"] == "TASK-003" 
