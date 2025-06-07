"""
Test Memory Querier
-----------------
Tests for the memory querier module.
"""

import pytest
import time
import json
from pathlib import Path
from dreamos.core.ai.dreamscribe import Dreamscribe
from dreamos.core.ai.memory_querier import MemoryQuerier

@pytest.fixture
def setup_teardown():
    """Setup and teardown for tests."""
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
    
    yield
    
    # Cleanup after tests
    for path in test_paths:
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                for file in path.glob("*"):
                    file.unlink()
                path.rmdir()

@pytest.fixture
def memory_querier():
    """Create a fresh MemoryQuerier instance for testing."""
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
    
    # Create Dreamscribe and MemoryQuerier instances
    dreamscribe = Dreamscribe()
    querier = MemoryQuerier(dreamscribe)
    
    # Add test memories with explicit timestamps
    current_time = time.time()
    test_memories = [
        {
            "timestamp": current_time - 3600,  # 1 hour ago
            "agent_id": "agent1",
            "content": "First test memory about Python",
            "context": {
                "source": "test",
                "type": "content_generated",
                "task_id": "TASK-001"
            },
            "insights": [
                {
                    "content": "Python is a popular language",
                    "confidence": 0.8
                }
            ],
            "connections": []
        },
        {
            "timestamp": current_time - 1800,  # 30 minutes ago
            "agent_id": "agent2",
            "content": "Second test memory about JavaScript",
            "context": {
                "source": "test",
                "type": "content_generated",
                "task_id": "TASK-002"
            },
            "insights": [
                {
                    "content": "JavaScript is used for web development",
                    "confidence": 0.9
                }
            ],
            "connections": []
        },
        {
            "timestamp": current_time - 900,  # 15 minutes ago
            "agent_id": "agent1",
            "content": "Third test memory about Python and JavaScript",
            "context": {
                "source": "test",
                "type": "content_generated",
                "task_id": "TASK-003"
            },
            "insights": [
                {
                    "content": "Both languages are important for web development",
                    "confidence": 0.7
                }
            ],
            "connections": []
        }
    ]
    
    # Ingest test memories and verify each ingestion
    for memory in test_memories:
        memory_id = dreamscribe.ingest_devlog(memory)
        assert memory_id is not None, f"Failed to ingest memory: {memory}"
        # Force save after each ingestion
        dreamscribe._save_memory_corpus()
    
    return querier

def test_get_recent_memory(memory_querier):
    """Test getting recent memories."""
    # Get all recent memories
    memories = memory_querier.get_recent_memory(limit=5)
    assert len(memories) == 3
    assert memories[0]["content"] == "Third test memory about Python and JavaScript"
    
    # Get agent-specific memories
    agent1_memories = memory_querier.get_recent_memory(agent_id="agent1", limit=5)
    assert len(agent1_memories) == 2
    assert all(m["agent_id"] == "agent1" for m in agent1_memories)
    
    # Get memories within time window (using 3601s to account for time drift)
    recent_memories = memory_querier.get_recent_memory(limit=5, time_window=3601)
    assert len(recent_memories) == 3
    
    # Test with a very small time window
    old_memories = memory_querier.get_recent_memory(time_window=100, limit=5)
    assert len(old_memories) == 0

def test_summarize_topic(memory_querier):
    """Test topic summarization."""
    # Summarize Python topic
    python_summary = memory_querier.summarize_topic("Python")
    assert python_summary["topic"] == "python"
    assert python_summary["memory_count"] == 2
    assert len(python_summary["key_insights"]) > 0
    assert "agent1" in python_summary["related_agents"]
    
    # Summarize JavaScript topic
    js_summary = memory_querier.summarize_topic("JavaScript")
    assert js_summary["topic"] == "javascript"
    assert js_summary["memory_count"] == 2
    assert len(js_summary["key_insights"]) > 0
    assert "agent2" in js_summary["related_agents"]
    
    # Test confidence threshold
    high_conf_summary = memory_querier.summarize_topic(
        "JavaScript",
        min_confidence=0.8
    )
    assert len(high_conf_summary["key_insights"]) == 1
    assert high_conf_summary["key_insights"][0]["confidence"] >= 0.8

def test_find_similar_threads(memory_querier):
    """Test finding similar threads."""
    # Get first memory ID
    memories = memory_querier.get_recent_memory(limit=1)
    memory_id = memories[0]["memory_id"]
    
    # Find similar threads
    similar = memory_querier.find_similar_threads(memory_id)
    assert len(similar) > 0
    
    # Test similarity threshold
    high_similarity = memory_querier.find_similar_threads(
        memory_id,
        min_similarity=0.9
    )
    assert len(high_similarity) <= len(similar)

def test_get_agent_insights(memory_querier):
    """Test getting agent insights."""
    # Get insights for agent1
    insights = memory_querier.get_agent_insights("agent1")
    assert len(insights) == 2
    assert all(i["agent_id"] == "agent1" for i in insights)
    
    # Test confidence threshold
    high_conf_insights = memory_querier.get_agent_insights(
        "agent1",
        min_confidence=0.8
    )
    assert len(high_conf_insights) == 1
    assert high_conf_insights[0]["confidence"] >= 0.8

def test_get_task_history(memory_querier):
    """Test getting task history."""
    # Get history for TASK-001
    history = memory_querier.get_task_history("TASK-001")
    assert history["task_id"] == "TASK-001"
    assert history["memory_count"] == 1
    assert len(history["memories"]) == 1
    
    # Test with related tasks
    history_with_related = memory_querier.get_task_history(
        "TASK-001",
        include_related=True
    )
    assert "related_tasks" in history_with_related
    assert "related_histories" in history_with_related 