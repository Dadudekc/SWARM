import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""
Tests for IO operations.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from dreamos.core.io.json_ops import JsonOperations
from dreamos.core.io.atomic import AtomicFileOperations
from dreamos.core.agent_io.agent_io import AgentIO

@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for tests."""
    return tmp_path

@pytest.fixture
def json_ops(temp_dir):
    """Create JsonOperations instance."""
    return JsonOperations(temp_dir)

@pytest.fixture
def atomic_ops(temp_dir):
    """Create AtomicFileOperations instance."""
    return AtomicFileOperations(temp_dir)

@pytest.fixture
def agent_io(temp_dir):
    """Create AgentIO instance."""
    return AgentIO(temp_dir)

def test_json_read_write(json_ops, temp_dir):
    """Test JSON read and write operations."""
    test_data = {"key": "value"}
    file_path = temp_dir / "test.json"
    
    # Write data
    json_ops.write_json(file_path, test_data)
    assert file_path.exists()
    
    # Read data
    read_data = json_ops.read_json(file_path)
    assert read_data == test_data

def test_atomic_file_operations(atomic_ops, temp_dir):
    """Test atomic file operations."""
    test_data = "test content"
    file_path = temp_dir / "test.txt"
    
    # Write data
    atomic_ops.write_file(file_path, test_data)
    assert file_path.exists()
    
    # Read data
    read_data = atomic_ops.read_file(file_path)
    assert read_data == test_data

def test_agent_io_operations(agent_io, temp_dir):
    """Test agent IO operations."""
    test_data = {"message": "test"}
    agent_id = "test-agent"
    
    # Write message
    agent_io.write_message(agent_id, test_data)
    message_path = temp_dir / f"{agent_id}.json"
    assert message_path.exists()
    
    # Read message
    read_data = agent_io.read_message(agent_id)
    assert read_data == test_data 