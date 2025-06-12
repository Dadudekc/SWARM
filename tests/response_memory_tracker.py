"""
Unit tests for ResponseMemoryTracker
-----------------------------------
Tests memory tracking, deduplication, and persistence functionality.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ..response_memory_tracker import ResponseMemoryTracker

@pytest.fixture
def temp_memory_file():
    """Create a temporary memory file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def memory_tracker(temp_memory_file):
    """Create a ResponseMemoryTracker instance with temporary storage."""
    return ResponseMemoryTracker(temp_memory_file)

@pytest.fixture
def sample_message() -> Dict[str, Any]:
    """Create a sample message for testing."""
    return {
        "agent_id": "test-agent-1",
        "type": "test_response",
        "content": "Test message content",
        "timestamp": datetime.now().isoformat()
    }

def test_initialization(memory_tracker, temp_memory_file):
    """Test memory tracker initialization."""
    assert memory_tracker.memory_path == Path(temp_memory_file)
    assert isinstance(memory_tracker.processed_hashes, set)
    assert len(memory_tracker.processed_hashes) == 0

def test_track_processing(memory_tracker, sample_message):
    """Test tracking message processing."""
    message_hash = "test_hash_123"
    
    # Track processing
    memory_tracker.track_processing(message_hash, sample_message)
    
    # Verify hash was added
    assert message_hash in memory_tracker.processed_hashes
    
    # Verify file was created and contains correct data
    with open(memory_tracker.memory_path, 'r') as f:
        data = json.load(f)
        assert "hashes" in data
        assert message_hash in data["hashes"]
        assert "metadata" in data
        assert data["metadata"] == sample_message

def test_is_processed(memory_tracker):
    """Test duplicate detection."""
    message_hash = "test_hash_456"
    
    # Initially not processed
    assert not memory_tracker.is_processed(message_hash)
    
    # Track processing
    memory_tracker.track_processing(message_hash)
    
    # Now should be processed
    assert memory_tracker.is_processed(message_hash)

def test_persistence(memory_tracker, sample_message):
    """Test memory persistence across instances."""
    message_hash = "test_hash_789"
    
    # Track with first instance
    memory_tracker.track_processing(message_hash, sample_message)
    
    # Create new instance with same file
    new_tracker = ResponseMemoryTracker(str(memory_tracker.memory_path))
    
    # Should recognize processed hash
    assert new_tracker.is_processed(message_hash)
    assert message_hash in new_tracker.processed_hashes

def test_invalid_file_handling():
    """Test handling of invalid memory file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        # Write invalid JSON
        f.write(b"invalid json content")
        f.flush()
        
        # Should handle gracefully
        tracker = ResponseMemoryTracker(f.name)
        assert isinstance(tracker.processed_hashes, set)
        assert len(tracker.processed_hashes) == 0

def test_get_stats(memory_tracker):
    """Test statistics retrieval."""
    # Add some hashes
    for i in range(3):
        memory_tracker.track_processing(f"hash_{i}")
    
    stats = memory_tracker.get_stats()
    assert "processed_count" in stats
    assert stats["processed_count"] == 3
    assert "memory_path" in stats
    assert "last_updated" in stats

def test_concurrent_access(memory_tracker):
    """Test concurrent access to memory tracker."""
    import threading
    
    def add_hash(hash_value):
        memory_tracker.track_processing(hash_value)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=add_hash, args=(f"concurrent_hash_{i}",))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Verify all hashes were added
    assert len(memory_tracker.processed_hashes) == 5
    for i in range(5):
        assert f"concurrent_hash_{i}" in memory_tracker.processed_hashes

def test_metadata_persistence(memory_tracker, sample_message):
    """Test persistence of processing metadata."""
    message_hash = "test_hash_metadata"
    metadata = {
        "processing_time_ms": 150,
        "agent_id": "test-agent-2",
        "status": "success"
    }
    
    # Track with metadata
    memory_tracker.track_processing(message_hash, metadata)
    
    # Create new instance
    new_tracker = ResponseMemoryTracker(str(memory_tracker.memory_path))
    
    # Verify metadata was persisted
    with open(new_tracker.memory_path, 'r') as f:
        data = json.load(f)
        assert "metadata" in data
        assert data["metadata"] == metadata

def test_error_handling(memory_tracker):
    """Test error handling in memory operations."""
    # Test with invalid hash
    memory_tracker.track_processing(None)
    assert len(memory_tracker.processed_hashes) == 0
    
    # Test with invalid metadata
    memory_tracker.track_processing("valid_hash", {"invalid": object()})
    assert "valid_hash" in memory_tracker.processed_hashes 
