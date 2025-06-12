"""
Test suite for AtomicFileManager

Validates atomic file operations, backup support, and recovery mechanisms.
"""

import os
import json
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from ..atomic_file_manager import AtomicFileManager
from .test_utils import (
    setup_test_environment,
    run_concurrent_operations,
    measure_operation_performance,
    create_test_state,
    create_test_task,
    PerformanceTimer,
    StateValidator
)

@pytest.fixture
async def atomic_manager(tmp_path):
    """Create a temporary atomic file manager for testing."""
    manager = AtomicFileManager(str(tmp_path / "test.json"))
    yield manager
    await manager.cleanup()

@pytest.mark.asyncio
async def test_atomic_write_success(atomic_manager, setup_test_environment, performance_timer):
    """Test successful atomic write operation with performance measurement."""
    test_data = {"test": "data"}
    
    # Measure write performance
    performance_timer.start()
    await atomic_manager.atomic_write(test_data)
    elapsed = performance_timer.stop()
    assert elapsed < 0.1  # Should complete within 100ms
    
    # Verify file exists and contains correct data
    assert atomic_manager.file_path.exists()
    with open(atomic_manager.file_path, 'r') as f:
        data = json.load(f)
    assert data == test_data

@pytest.mark.asyncio
async def test_atomic_write_with_backup(atomic_manager, setup_test_environment):
    """Test atomic write with backup creation."""
    # Write initial data
    initial_data = {"initial": "data"}
    await atomic_manager.atomic_write(initial_data)
    
    # Write new data
    new_data = {"new": "data"}
    await atomic_manager.atomic_write(new_data)
    
    # Verify backup exists and contains initial data
    assert atomic_manager.backup_path.exists()
    with open(atomic_manager.backup_path, 'r') as f:
        backup_data = json.load(f)
    assert backup_data == initial_data

@pytest.mark.asyncio
async def test_atomic_read_success(atomic_manager, setup_test_environment, performance_timer):
    """Test successful atomic read operation with performance measurement."""
    test_data = {"test": "data"}
    await atomic_manager.atomic_write(test_data)
    
    # Measure read performance
    performance_timer.start()
    data = await atomic_manager.atomic_read()
    elapsed = performance_timer.stop()
    assert elapsed < 0.1  # Should complete within 100ms
    
    assert data == test_data

@pytest.mark.asyncio
async def test_atomic_read_recovery(atomic_manager, setup_test_environment):
    """Test recovery from backup after file corruption."""
    # Write initial data
    initial_data = {"initial": "data"}
    await atomic_manager.atomic_write(initial_data)
    
    # Corrupt main file
    setup_test_environment.corrupt_state_file()
    
    # Read should recover from backup
    data = await atomic_manager.atomic_read()
    assert data == initial_data

@pytest.mark.asyncio
async def test_concurrent_writes(atomic_manager, setup_test_environment):
    """Test concurrent write operations."""
    async def write_operation():
        await atomic_manager.atomic_write({"count": 1})
    
    await run_concurrent_operations(write_operation)
    
    # Verify final state
    data = await atomic_manager.atomic_read()
    assert data is not None
    assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_file_validation(atomic_manager, setup_test_environment, state_validator):
    """Test file validation functionality."""
    # Write valid data
    valid_data = create_test_state()
    await atomic_manager.atomic_write(valid_data)
    assert await atomic_manager.validate_file()
    assert state_validator.validate_state_structure(valid_data)
    
    # Write invalid data
    setup_test_environment.corrupt_state_file()
    assert not await atomic_manager.validate_file()

@pytest.mark.asyncio
async def test_recovery_from_backup(atomic_manager, setup_test_environment):
    """Test recovery from backup file."""
    # Write initial data
    initial_data = {"initial": "data"}
    await atomic_manager.atomic_write(initial_data)
    
    # Corrupt main file
    setup_test_environment.corrupt_state_file()
    
    # Attempt recovery
    recovered = await atomic_manager._recover_from_backup()
    assert recovered
    assert await atomic_manager.atomic_read() == initial_data

@pytest.mark.asyncio
async def test_cleanup(atomic_manager, setup_test_environment):
    """Test cleanup of temporary files."""
    # Write some data
    await atomic_manager.atomic_write({"test": "data"})
    
    # Verify files exist
    assert atomic_manager.file_path.exists()
    assert atomic_manager.backup_path.exists()
    
    # Cleanup
    await atomic_manager.cleanup()
    
    # Verify temporary files are removed
    assert not atomic_manager.temp_path.exists()

@pytest.mark.asyncio
async def test_write_failure_handling(atomic_manager, setup_test_environment):
    """Test handling of write failures."""
    # Make directory read-only to simulate write failure
    atomic_manager.file_path.parent.chmod(0o444)
    
    try:
        # Attempt write
        with pytest.raises(Exception):
            await atomic_manager.atomic_write({"test": "data"})
    finally:
        # Restore permissions
        atomic_manager.file_path.parent.chmod(0o755)

@pytest.mark.asyncio
async def test_retry_mechanism(atomic_manager, setup_test_environment):
    """Test retry mechanism for failed operations."""
    # Write initial data
    initial_data = {"initial": "data"}
    await atomic_manager.atomic_write(initial_data)
    
    # Corrupt main file
    setup_test_environment.corrupt_state_file()
    
    # Attempt read with retry
    data = await atomic_manager.atomic_read()
    assert data == initial_data

@pytest.mark.asyncio
async def test_performance_under_load(atomic_manager, setup_test_environment):
    """Test performance under load."""
    async def load_operation():
        await atomic_manager.atomic_write({"load": "test"})
        await atomic_manager.atomic_read()
        await asyncio.sleep(0.01)  # Simulate work
    
    # Measure performance under load
    performance = await measure_operation_performance(load_operation, iterations=10)
    assert performance["average"] < 0.2  # Should handle load within 200ms
    assert performance["max"] < 0.5  # No operation should take more than 500ms

@pytest.mark.asyncio
async def test_random_corruption(atomic_manager, setup_test_environment):
    """Test handling of random file corruption."""
    # Write initial data
    initial_data = {"initial": "data"}
    await atomic_manager.atomic_write(initial_data)
    
    # Simulate random corruption
    setup_test_environment.simulate_file_corruption(probability=0.5)
    
    # Attempt read
    data = await atomic_manager.atomic_read()
    assert data is not None  # Should either read original or recover from backup 
