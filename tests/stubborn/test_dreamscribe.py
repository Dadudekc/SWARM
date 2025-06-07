"""
Test suite for Dreamscribe memory system.
"""

import pytest
import time
from pathlib import Path
from dreamos.core.ai.dreamscribe import Dreamscribe, MemoryFragment, NarrativeThread

@pytest.fixture
def dreamscribe():
    """Create a fresh Dreamscribe instance for testing."""
    # Clear any existing test data
    test_paths = [
        Path("runtime/memory_corpus.json"),
        Path("runtime/insight_patterns.json"),
        Path("runtime/narrative_threads")
    ]
    
    for path in test_paths:
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                for file in path.glob("*"):
                    file.unlink()
                path.rmdir()
    
    return Dreamscribe()

def test_memory_ingestion(dreamscribe):
    """Test basic memory ingestion."""
    # Create test devlog
    devlog = {
        "timestamp": time.time(),
        "agent_id": "test_agent",
        "content": "Test task completed successfully",
        "context": {"task_id": "123", "type": "test"}
    }
    
    # Ingest memory
    memory_id = dreamscribe.ingest_devlog(devlog)
    
    # Verify memory was created
    memory = dreamscribe.get_memory(memory_id)
    assert memory is not None
    assert memory.agent_id == "test_agent"
    assert "success" in memory.content.lower()
    assert len(memory.insights) > 0
    
    # Verify system insights
    insights = dreamscribe.get_system_insights()
    assert insights["memory_state"]["total_memories"] == 1
    assert len(insights["narratives"]) > 0

def test_narrative_threading(dreamscribe):
    """Test narrative thread creation and updates."""
    # Create sequence of related devlogs
    devlogs = [
        {
            "timestamp": time.time(),
            "agent_id": "test_agent",
            "content": "Starting new task",
            "context": {"task_id": "123"}
        },
        {
            "timestamp": time.time() + 1,
            "agent_id": "test_agent",
            "content": "Task in progress",
            "context": {"task_id": "123"}
        },
        {
            "timestamp": time.time() + 2,
            "agent_id": "test_agent",
            "content": "Task completed successfully",
            "context": {"task_id": "123"}
        }
    ]
    
    # Ingest memories
    memory_ids = []
    for devlog in devlogs:
        memory_id = dreamscribe.ingest_devlog(devlog)
        memory_ids.append(memory_id)
    
    # Verify narrative thread was created
    insights = dreamscribe.get_system_insights()
    assert len(insights["narratives"]) > 0
    
    # Get the thread
    thread = dreamscribe.get_thread(insights["narratives"][0]["thread_id"])
    assert thread is not None
    assert len(thread.memories) == 3

def test_insight_patterns(dreamscribe):
    """Test insight pattern detection and tracking."""
    # Create devlogs with different patterns
    devlogs = [
        {
            "timestamp": time.time(),
            "agent_id": "test_agent",
            "content": "Error encountered: connection timeout",
            "context": {"task_id": "123"}
        },
        {
            "timestamp": time.time() + 1,
            "agent_id": "test_agent",
            "content": "Error resolved: connection restored",
            "context": {"task_id": "123"}
        }
    ]
    
    # Ingest memories
    for devlog in devlogs:
        dreamscribe.ingest_devlog(devlog)
    
    # Verify insight patterns
    insights = dreamscribe.get_system_insights()
    assert "patterns" in insights
    assert len(insights["patterns"]) > 0
    
    # Check for error-related insights
    error_insights = [
        p for p in insights["patterns"]
        if "error" in p.lower()
    ]
    assert len(error_insights) > 0

def test_memory_connections(dreamscribe):
    """Test memory connection detection."""
    # Create related devlogs
    base_time = time.time()
    devlogs = [
        {
            "timestamp": base_time,
            "agent_id": "test_agent",
            "content": "Initial state",
            "context": {"task_id": "123"}
        },
        {
            "timestamp": base_time + 30,  # Within 1 hour
            "agent_id": "test_agent",
            "content": "Related state",
            "context": {"task_id": "123"}
        },
        {
            "timestamp": base_time + 7200,  # 2 hours later
            "agent_id": "test_agent",
            "content": "Unrelated state",
            "context": {"task_id": "456"}
        }
    ]
    
    # Ingest memories
    memory_ids = []
    for devlog in devlogs:
        memory_id = dreamscribe.ingest_devlog(devlog)
        memory_ids.append(memory_id)
    
    # Verify connections
    memory1 = dreamscribe.get_memory(memory_ids[0])
    memory2 = dreamscribe.get_memory(memory_ids[1])
    memory3 = dreamscribe.get_memory(memory_ids[2])
    
    assert memory1 is not None and memory2 is not None and memory3 is not None
    assert len(memory1.connections) > 0  # Should connect to memory2
    assert len(memory3.connections) == 0  # Should not connect to others 