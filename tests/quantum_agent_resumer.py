"""
Tests for QuantumAgentResumer

Validates system integration, health checks, and recovery mechanisms.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from ..quantum_agent_resumer import QuantumAgentResumer
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
async def quantum_resumer(tmp_path):
    """Create a temporary quantum resumer for testing."""
    resumer = QuantumAgentResumer(str(tmp_path))
    await resumer.start()
    yield resumer
    await resumer.stop()

@pytest.mark.asyncio
async def test_system_initialization(quantum_resumer, state_validator):
    """Test system initialization."""
    state = await quantum_resumer.state_manager.get_state()
    assert state is not None
    assert state_validator.validate_state_structure(state)
    assert state["mode"] == "normal"
    assert not state["test_debug"]["active"]

@pytest.mark.asyncio
async def test_test_debug_mode(quantum_resumer, state_validator):
    """Test test debug mode activation."""
    old_state = await quantum_resumer.state_manager.get_state()
    await quantum_resumer.activate_test_debug_mode()
    
    new_state = await quantum_resumer.state_manager.get_state()
    assert state_validator.validate_state_structure(new_state)
    assert state_validator.validate_state_transition(old_state, new_state)
    assert new_state["mode"] == "test_debug"
    assert new_state["test_debug"]["active"]
    assert new_state["test_debug"]["start_time"] is not None

@pytest.mark.asyncio
async def test_cycle_increment(quantum_resumer, state_validator, performance_timer):
    """Test cycle increment functionality with performance measurement."""
    initial_state = await quantum_resumer.state_manager.get_state()
    initial_count = initial_state["cycle_count"]
    
    # Measure performance of cycle increment
    performance_timer.start()
    await quantum_resumer.increment_cycle()
    elapsed = performance_timer.stop()
    assert elapsed < 0.1  # Should complete within 100ms
    
    new_state = await quantum_resumer.state_manager.get_state()
    assert state_validator.validate_state_structure(new_state)
    assert state_validator.validate_state_transition(initial_state, new_state)
    assert new_state["cycle_count"] == initial_count + 1
    assert new_state["last_active"] is not None

@pytest.mark.asyncio
async def test_task_management(quantum_resumer, setup_test_environment, state_validator):
    """Test task management operations."""
    # Add test fix task
    test_fix_data = {
        "description": "Test fix task",
        "priority": "high"
    }
    task = await quantum_resumer.add_test_fix_task(test_fix_data)
    
    # Validate task structure
    assert state_validator.validate_task_structure(task)
    assert task["type"] == "TEST_FIX"
    assert task["status"] == "pending"
    
    # Add blocker task
    blocker_data = {
        "description": "Blocker task",
        "severity": "critical"
    }
    blocker = await quantum_resumer.add_blocker_task(blocker_data)
    
    # Verify tasks
    tasks = await quantum_resumer.state_manager.get_tasks()
    assert "TEST_FIX" in tasks
    assert "BLOCKER-TEST-DEBUG" in tasks
    assert len(tasks["TEST_FIX"]) == 1
    assert len(tasks["BLOCKER-TEST-DEBUG"]) == 1
    
    # Validate task transitions
    assert state_validator.validate_task_structure(blocker)
    assert blocker["type"] == "BLOCKER-TEST-DEBUG"

@pytest.mark.asyncio
async def test_health_check_recovery(quantum_resumer, setup_test_environment, state_validator):
    """Test health check recovery mechanism."""
    # Corrupt state file
    setup_test_environment.corrupt_state_file()
    
    # Wait for health check
    await asyncio.sleep(2)
    
    # Verify recovery
    state = await quantum_resumer.state_manager.get_state()
    assert state is not None
    assert state_validator.validate_state_structure(state)

@pytest.mark.asyncio
async def test_metrics_tracking(quantum_resumer, performance_timer):
    """Test metrics tracking with performance measurement."""
    # Measure performance of operations
    async def test_operations():
        await quantum_resumer.increment_cycle()
        await quantum_resumer.add_test_fix_task({"test": "data"})
    
    performance = await measure_operation_performance(test_operations)
    assert performance["average"] < 0.2  # Should complete within 200ms
    
    # Verify metrics
    assert quantum_resumer.metrics["cycle_count"] > 0
    assert quantum_resumer.metrics["last_health_check"] is not None

@pytest.mark.asyncio
async def test_concurrent_operations(quantum_resumer, state_validator):
    """Test concurrent operations with validation."""
    async def increment_and_add_task():
        await quantum_resumer.increment_cycle()
        await quantum_resumer.add_test_fix_task({"task": "data"})
    
    await run_concurrent_operations(increment_and_add_task)
    
    # Verify results
    state = await quantum_resumer.state_manager.get_state()
    assert state_validator.validate_state_structure(state)
    assert state["cycle_count"] == 5
    
    tasks = await quantum_resumer.state_manager.get_tasks()
    assert len(tasks["TEST_FIX"]) == 5

@pytest.mark.asyncio
async def test_system_shutdown(quantum_resumer, state_validator):
    """Test system shutdown with state validation."""
    # Perform some operations
    await quantum_resumer.increment_cycle()
    await quantum_resumer.add_test_fix_task({"test": "data"})
    
    # Capture final state
    final_state = await quantum_resumer.state_manager.get_state()
    assert state_validator.validate_state_structure(final_state)
    
    # Stop system
    await quantum_resumer.stop()
    
    # Verify cleanup
    assert quantum_resumer.health_check_task.cancelled()

@pytest.mark.asyncio
async def test_error_recovery(quantum_resumer, setup_test_environment, state_validator):
    """Test error recovery mechanisms with state validation."""
    # Simulate state corruption
    setup_test_environment.corrupt_state_file()
    
    # Attempt operations
    await quantum_resumer.increment_cycle()
    await quantum_resumer.add_test_fix_task({"test": "data"})
    
    # Verify system recovered
    state = await quantum_resumer.state_manager.get_state()
    assert state is not None
    assert state_validator.validate_state_structure(state)
    assert state["cycle_count"] > 0

@pytest.mark.asyncio
async def test_debug_logging(quantum_resumer, setup_test_environment):
    """Test debug logging functionality."""
    # Log some messages
    await quantum_resumer.state_manager.log_debug("Test message 1")
    await quantum_resumer.state_manager.log_debug("Test message 2")
    
    # Verify logs
    log_file = quantum_resumer.base_dir / "debug_logs/test_debug.log"
    assert log_file.exists()

@pytest.mark.asyncio
async def test_state_validation(quantum_resumer, setup_test_environment, state_validator):
    """Test state validation during operations."""
    # Corrupt state
    setup_test_environment.corrupt_state_file('{"invalid": "state"}')
    
    # Attempt operation
    await quantum_resumer.increment_cycle()
    
    # Verify state was recovered
    state = await quantum_resumer.state_manager.get_state()
    assert state_validator.validate_state_structure(state)

@pytest.mark.asyncio
async def test_event_handling(quantum_resumer, mock_event_collector):
    """Test event handling with mock collector."""
    # Register event handlers
    quantum_resumer.state_manager.register_event_handler(
        "state_update",
        mock_event_collector.collect_event
    )
    
    # Perform operations that trigger events
    await quantum_resumer.increment_cycle()
    await quantum_resumer.add_test_fix_task({"test": "data"})
    
    # Verify events were collected
    state_events = mock_event_collector.get_events_by_type("state_update")
    assert len(state_events) > 0

@pytest.mark.asyncio
async def test_performance_under_load(quantum_resumer, performance_timer):
    """Test system performance under load."""
    async def load_operation():
        await quantum_resumer.increment_cycle()
        await quantum_resumer.add_test_fix_task({"load": "test"})
        await asyncio.sleep(0.01)  # Simulate work
    
    # Measure performance under load
    performance = await measure_operation_performance(load_operation, iterations=10)
    assert performance["average"] < 0.5  # Should handle load within 500ms
    assert performance["max"] < 1.0  # No operation should take more than 1s 
