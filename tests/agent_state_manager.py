"""
Test suite for AgentStateManager

Validates state management, event handling, and task operations.
"""

import asyncio
import pytest
import pytest_asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from dreamos.core.resumer_v2.agent_state_manager import AgentStateManager, TaskData
from dreamos.core.messaging.enums import TaskStatus
from .test_utils import (
    setup_test_environment,
    run_concurrent_operations,
    measure_operation_performance,
    create_test_state,
    create_test_task,
    MockEventCollector,
    PerformanceTimer,
    StateValidator
)

@pytest.fixture
async def state_manager(tmp_path):
    """Create a temporary state manager for testing."""
    manager = AgentStateManager(str(tmp_path))
    await manager._init_state()
    yield manager
    await manager.cleanup()

@pytest.mark.asyncio
async def test_initialization(state_manager, setup_test_environment, state_validator):
    """Test state initialization."""
    state = await state_manager.get_state()
    assert state is not None
    assert state_validator.validate_state_structure(state)
    assert state["mode"] == "normal"
    assert not state["test_debug"]["active"]

@pytest.mark.asyncio
async def test_state_update(state_manager, setup_test_environment, state_validator):
    """Test state update functionality with validation."""
    old_state = await state_manager.get_state()
    new_state = create_test_state(
        cycle_count=1,
        mode="test",
        test_debug={
            "active": True,
            "start_time": datetime.now().isoformat()
        }
    )
    
    await state_manager.update_state(new_state)
    
    current_state = await state_manager.get_state()
    assert state_validator.validate_state_structure(current_state)
    assert state_validator.validate_state_transition(old_state, current_state)
    assert current_state["cycle_count"] == 1
    assert current_state["mode"] == "test"
    assert current_state["test_debug"]["active"]

@pytest.mark.asyncio
async def test_event_handling(state_manager, setup_test_environment, mock_event_collector):
    """Test event handling system with mock collector."""
    # Register handler
    state_manager.register_event_handler("state_update", mock_event_collector.collect_event)
    
    # Trigger event
    new_state = {"cycle_count": 1}
    await state_manager.update_state(new_state)
    
    # Verify event was received
    state_events = mock_event_collector.get_events_by_type("state_update")
    assert len(state_events) == 1
    assert state_events[0][1] == new_state

@pytest.mark.asyncio
async def test_task_management(state_manager, setup_test_environment, state_validator):
    """Test task management operations with validation."""
    # Add task
    task_data = {
        "description": "Test task",
        "priority": "high"
    }
    task = await state_manager.add_task("TEST", task_data)
    
    # Validate task
    assert state_validator.validate_task_structure(task)
    assert task["type"] == "TEST"
    assert task["status"] == "pending"
    
    # Update task
    updated_task = await state_manager.update_task(
        task["id"],
        "in_progress",
        {"progress": 50}
    )
    
    # Validate task transition
    assert state_validator.validate_task_transition(task, updated_task)
    assert updated_task["status"] == "in_progress"
    assert updated_task["data"]["progress"] == 50

@pytest.mark.asyncio
async def test_task_filtering(state_manager, setup_test_environment):
    """Test task filtering by type."""
    # Add multiple tasks
    tasks = setup_test_environment.create_test_tasks(5, "TEST")
    for task in tasks:
        await state_manager.add_task("TEST", task["data"])
    
    await state_manager.add_task("OTHER", {"other": "1"})
    
    # Filter tasks
    test_tasks = await state_manager.get_tasks_by_type("TEST")
    assert len(test_tasks) == 5
    assert all(task["type"] == "TEST" for task in test_tasks)

@pytest.mark.asyncio
async def test_debug_logging(state_manager, setup_test_environment):
    """Test debug logging functionality."""
    # Log messages
    await state_manager.log_debug("Test message 1")
    await state_manager.log_debug("Test message 2")
    
    # Verify log file
    log_file = state_manager.base_dir / "debug_logs/test_debug.log"
    assert log_file.exists()

@pytest.mark.asyncio
async def test_state_validation(state_manager, setup_test_environment, state_validator):
    """Test state validation."""
    # Valid state
    valid_state = create_test_state()
    assert state_validator.validate_state_structure(valid_state)
    
    # Invalid state
    invalid_state = {"invalid": "state"}
    assert not state_validator.validate_state_structure(invalid_state)

@pytest.mark.asyncio
async def test_concurrent_operations(state_manager, setup_test_environment, state_validator):
    """Test concurrent state and task operations."""
    async def update_operation():
        await state_manager.update_state({"cycle_count": 1})
        await state_manager.add_task("TEST", {"test": "data"})
    
    await run_concurrent_operations(update_operation)
    
    # Verify final state
    state = await state_manager.get_state()
    assert state_validator.validate_state_structure(state)
    assert state["cycle_count"] > 0
    
    tasks = await state_manager.get_tasks()
    assert len(tasks["TEST"]) > 0

@pytest.mark.asyncio
async def test_error_handling(state_manager, setup_test_environment, mock_event_collector):
    """Test error handling in event system."""
    # Register error handler
    state_manager.register_event_handler("error", mock_event_collector.collect_event)
    
    # Simulate error
    await state_manager.dispatch_event("error", {"message": "Test error"})
    
    # Verify error was collected
    error_events = mock_event_collector.get_events_by_type("error")
    assert len(error_events) == 1
    assert error_events[0][1]["message"] == "Test error"

@pytest.mark.asyncio
async def test_performance_under_load(state_manager, setup_test_environment):
    """Test performance under load."""
    async def load_operation():
        await state_manager.update_state({"cycle_count": 1})
        await state_manager.add_task("TEST", {"load": "test"})
        await asyncio.sleep(0.01)  # Simulate work
    
    # Measure performance under load
    performance = await measure_operation_performance(load_operation, iterations=10)
    assert performance["average"] < 0.2  # Should handle load within 200ms
    assert performance["max"] < 0.5  # No operation should take more than 500ms

@pytest.mark.asyncio
async def test_task_state_transitions(state_manager, setup_test_environment, state_validator):
    """Test task state transition validation."""
    # Create initial task
    task = await state_manager.add_task("TEST", {"test": "data"})
    assert task["status"] == "pending"
    
    # Test valid transitions
    valid_transitions = [
        ("in_progress", {"progress": 0}),
        ("completed", {"result": "success"}),
        ("failed", {"error": "test error"})
    ]
    
    current_task = task
    for new_status, new_data in valid_transitions:
        updated_task = await state_manager.update_task(
            current_task["id"],
            new_status,
            new_data
        )
        assert state_validator.validate_task_transition(current_task, updated_task)
        current_task = updated_task
    
    # Test invalid transition
    with pytest.raises(ValueError):
        await state_manager.update_task(
            current_task["id"],
            "pending",  # Can't go back to pending from completed
            {"test": "data"}
        ) 
