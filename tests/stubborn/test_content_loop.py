"""
Test suite for Content Loop integration with Dreamscribe.
"""

import pytest
import time
from pathlib import Path
from dreamos.core.autonomy.content_loop import ContentLoop

@pytest.fixture
def content_loop():
    """Create a fresh ContentLoop instance for testing."""
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
    
    return ContentLoop()

def test_content_event_logging(content_loop):
    """Test basic content event logging."""
    # Log a content generation event
    memory_id = content_loop.log_content_event(
        agent_id="test_agent",
        task_id="123",
        content="Test content generation",
        event_type="content_generated"
    )
    
    # Verify memory was created
    history = content_loop.get_content_history(
        agent_id="test_agent",
        task_id="123",
        event_type="content_generated"
    )
    
    assert len(history) == 1
    assert history[0]["memory_id"] == memory_id
    assert history[0]["content"] == "Test content generation"
    assert history[0]["context"]["type"] == "content_generated"

def test_task_completion_logging(content_loop):
    """Test task completion logging."""
    # Log a task completion
    memory_id = content_loop.log_task_completion(
        agent_id="test_agent",
        task_id="123",
        result="Task completed successfully",
        metadata={"status": "success"}
    )
    
    # Verify memory was created
    history = content_loop.get_content_history(
        agent_id="test_agent",
        task_id="123",
        event_type="task_completed"
    )
    
    assert len(history) == 1
    assert history[0]["memory_id"] == memory_id
    assert history[0]["content"] == "Task completed successfully"
    assert history[0]["context"]["type"] == "task_completed"
    assert history[0]["context"]["status"] == "success"

def test_insight_logging(content_loop):
    """Test insight logging."""
    # Log an insight
    memory_id = content_loop.log_insight(
        agent_id="test_agent",
        task_id="123",
        insight="System pattern detected",
        confidence=0.8,
        metadata={"pattern_type": "recurring"}
    )
    
    # Verify memory was created
    history = content_loop.get_content_history(
        agent_id="test_agent",
        task_id="123",
        event_type="insight_detected"
    )
    
    assert len(history) == 1
    assert history[0]["memory_id"] == memory_id
    assert history[0]["content"] == "System pattern detected"
    assert history[0]["context"]["type"] == "insight_detected"
    assert history[0]["context"]["confidence"] == 0.8
    assert history[0]["context"]["pattern_type"] == "recurring"

def test_content_history_filtering(content_loop):
    """Test content history filtering."""
    # Log multiple events
    content_loop.log_content_event(
        agent_id="agent1",
        task_id="task1",
        content="Content 1",
        event_type="content_generated"
    )
    
    content_loop.log_content_event(
        agent_id="agent2",
        task_id="task1",
        content="Content 2",
        event_type="content_generated"
    )
    
    content_loop.log_content_event(
        agent_id="agent1",
        task_id="task2",
        content="Content 3",
        event_type="content_generated"
    )
    
    # Test filtering by agent
    agent1_history = content_loop.get_content_history(agent_id="agent1")
    assert len(agent1_history) == 2
    
    # Test filtering by task
    task1_history = content_loop.get_content_history(task_id="task1")
    assert len(task1_history) == 2
    
    # Test filtering by both
    filtered_history = content_loop.get_content_history(
        agent_id="agent1",
        task_id="task1"
    )
    assert len(filtered_history) == 1
    assert filtered_history[0]["content"] == "Content 1"

def test_invalid_event_type(content_loop):
    """Test handling of invalid event types."""
    with pytest.raises(ValueError):
        content_loop.log_content_event(
            agent_id="test_agent",
            task_id="123",
            content="Test content",
            event_type="invalid_type"
        ) 
