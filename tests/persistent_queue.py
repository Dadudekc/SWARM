"""
Tests for the persistent queue module.
"""

import pytest
from dreamos.core.shared.persistent_queue import (
    PersistentQueue,
    load_queue,
    save_queue
)

def test_queue_initialization():
    """Test that PersistentQueue initializes correctly."""
    queue = PersistentQueue()
    assert queue is not None
    assert isinstance(queue, PersistentQueue)
    assert len(queue) == 0

def test_queue_operations():
    """Test basic queue operations."""
    queue = PersistentQueue()
    
    # Test enqueue
    test_item = "test_item"
    queue.enqueue(test_item)
    assert len(queue) == 1
    
    # Test dequeue
    dequeued_item = queue.dequeue()
    assert dequeued_item == test_item
    assert len(queue) == 0
    
    # Test empty queue
    with pytest.raises(IndexError):
        queue.dequeue()

def test_queue_persistence():
    """Test queue persistence operations."""
    queue = PersistentQueue()
    
    # Add items
    queue.enqueue("item1")
    queue.enqueue("item2")
    
    # Save queue
    save_queue(queue)
    
    # Create new queue and load
    new_queue = PersistentQueue()
    load_queue(new_queue)
    
    # Verify items
    assert len(new_queue) == 2
    assert new_queue.dequeue() == "item1"
    assert new_queue.dequeue() == "item2" 