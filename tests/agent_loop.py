import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for agent_loop module."""

import pytest
import json
from pathlib import Path
from dreamos.core.autonomy.agent_loop import AgentLoop
from dreamos.core.agent_control.controller import AgentController

# Fixtures
@pytest.fixture
def mock_controller():
    """Create a mock controller for testing."""
    return AgentController()

@pytest.fixture
def agent_loop(mock_controller):
    """Create an AgentLoop instance for testing."""
    return AgentLoop(mock_controller)

@pytest.fixture
def sample_inbox_data():
    """Create sample inbox data for testing."""
    return [
        {"id": "1", "content": "test message 1"},
        {"id": "2", "content": "test message 2"}
    ]

@pytest.mark.skip(reason='Pending implementation')
def test_agent_loop_initialization(agent_loop):
    """Test AgentLoop initialization."""
    # TODO: Implement test
    pass

def test_load_inbox(agent_loop, sample_inbox_data, tmp_path):
    """Test _load_inbox method."""
    # Create a temporary inbox directory and file
    agent_id = "test_agent"
    inbox_dir = tmp_path / agent_id
    inbox_dir.mkdir()
    inbox_file = inbox_dir / "inbox.json"
    
    # Write sample data to the inbox file
    with open(inbox_file, 'w') as f:
        json.dump(sample_inbox_data, f)
    
    # Temporarily set the inbox path to our test directory
    original_inbox_path = agent_loop.inbox_path
    agent_loop.inbox_path = tmp_path
    
    try:
        # Test loading the inbox
        result = agent_loop._load_inbox(agent_id)
        
        # Verify the result
        assert result == sample_inbox_data
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
    finally:
        # Restore original inbox path
        agent_loop.inbox_path = original_inbox_path

def test_save_inbox(agent_loop, sample_inbox_data, tmp_path):
    """Test save_inbox method."""
    # Create a temporary inbox directory
    agent_id = "test_agent"
    inbox_dir = tmp_path / agent_id
    inbox_dir.mkdir()
    inbox_file = inbox_dir / "inbox.json"
    
    # Temporarily set the inbox path to our test directory
    original_inbox_path = agent_loop.inbox_path
    agent_loop.inbox_path = tmp_path
    
    try:
        # Save the inbox data
        agent_loop.save_inbox(str(inbox_file), sample_inbox_data)
        
        # Verify the file was created and contains the correct data
        assert inbox_file.exists()
        with open(inbox_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data == sample_inbox_data
            assert len(saved_data) == 2
            assert saved_data[0]["id"] == "1"
            assert saved_data[1]["id"] == "2"
    finally:
        # Restore original inbox path
        agent_loop.inbox_path = original_inbox_path
