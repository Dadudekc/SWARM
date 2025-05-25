import os
import json
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from pathlib import Path

from social.dispatcher import TaskDispatcher
from social.social_config import SocialConfig

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return Mock(spec=SocialConfig)

@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    with patch('social.utils.log_manager.LogManager') as mock:
        yield mock

@pytest.fixture
def task_dispatcher(mock_config, mock_logger):
    """Create a TaskDispatcher instance with mocked dependencies."""
    return TaskDispatcher(mock_config)

def test_init(task_dispatcher, mock_config):
    """Test TaskDispatcher initialization."""
    assert task_dispatcher.config == mock_config
    assert isinstance(task_dispatcher.tasks, list)
    assert task_dispatcher.memory_updates["tasks_dispatched"] == 0
    assert task_dispatcher.memory_updates["tasks_completed"] == 0
    assert task_dispatcher.memory_updates["tasks_failed"] == 0

def test_load_tasks_success(task_dispatcher, mock_logger):
    """Test successful task loading."""
    mock_tasks = [
        {"type": "post", "platform": "twitter", "content": "Test post"},
        {"type": "comment", "platform": "reddit", "content": "Test comment"}
    ]
    
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_tasks))):
        with patch('pathlib.Path.exists', return_value=True):
            result = task_dispatcher.load_tasks()
            
            assert result is True
            assert task_dispatcher.tasks == mock_tasks
            assert task_dispatcher.memory_updates["last_action"]["action"] == "load_tasks"
            assert task_dispatcher.memory_updates["last_action"]["success"] is True

def test_load_tasks_file_not_found(task_dispatcher, mock_logger):
    """Test task loading when file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = task_dispatcher.load_tasks()
        
        assert result is False
        assert task_dispatcher.memory_updates["last_action"]["action"] == "load_tasks"
        assert task_dispatcher.memory_updates["last_action"]["success"] is False
        assert "Task list file not found" in str(task_dispatcher.memory_updates["last_error"]["error"])

def test_add_task_success(task_dispatcher, mock_logger):
    """Test successful task addition."""
    task = {"type": "post", "platform": "twitter", "content": "Test post"}
    result = task_dispatcher.add_task(task)
    
    assert result is True
    assert task in task_dispatcher.tasks
    assert task_dispatcher.memory_updates["last_action"]["action"] == "add_task"
    assert task_dispatcher.memory_updates["last_action"]["success"] is True

def test_dispatch_task_success(task_dispatcher, mock_logger):
    """Test successful task dispatch."""
    task = {"type": "post", "platform": "twitter", "content": "Test post"}
    handler = Mock(return_value=True)
    
    result = task_dispatcher.dispatch_task(task, handler)
    
    assert result is True
    assert task_dispatcher.memory_updates["tasks_dispatched"] == 1
    assert task_dispatcher.memory_updates["tasks_completed"] == 1
    assert task_dispatcher.memory_updates["last_action"]["action"] == "dispatch_task"
    assert task_dispatcher.memory_updates["last_action"]["success"] is True
    handler.assert_called_once_with(task)

def test_dispatch_task_failure(task_dispatcher, mock_logger):
    """Test failed task dispatch."""
    task = {"type": "post", "platform": "twitter", "content": "Test post"}
    handler = Mock(return_value=False)
    
    result = task_dispatcher.dispatch_task(task, handler)
    
    assert result is False
    assert task_dispatcher.memory_updates["tasks_dispatched"] == 1
    assert task_dispatcher.memory_updates["tasks_failed"] == 1
    assert task_dispatcher.memory_updates["last_action"]["action"] == "dispatch_task"
    assert task_dispatcher.memory_updates["last_action"]["success"] is False
    assert "Task handler returned False" in str(task_dispatcher.memory_updates["last_error"]["error"])

def test_get_next_task(task_dispatcher):
    """Test getting next task from queue."""
    task1 = {"type": "post", "platform": "twitter", "content": "Test post 1"}
    task2 = {"type": "post", "platform": "twitter", "content": "Test post 2"}
    task_dispatcher.tasks = [task1, task2]
    
    next_task = task_dispatcher.get_next_task()
    assert next_task == task1
    assert task_dispatcher.tasks == [task2]
    
    next_task = task_dispatcher.get_next_task()
    assert next_task == task2
    assert task_dispatcher.tasks == []
    
    next_task = task_dispatcher.get_next_task()
    assert next_task is None

def test_get_memory_updates(task_dispatcher):
    """Test getting memory updates."""
    memory = task_dispatcher.get_memory_updates()
    assert isinstance(memory, dict)
    assert "tasks_dispatched" in memory
    assert "tasks_completed" in memory
    assert "tasks_failed" in memory
    assert "last_action" in memory
    assert "last_error" in memory 