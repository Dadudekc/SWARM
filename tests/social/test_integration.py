import os
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path

from social.dispatcher import TaskDispatcher
from social.social_config import SocialConfig
from social.utils.log_manager import LogManager

@pytest.fixture
def mock_config_data():
    """Create mock configuration data."""
    return {
        "twitter": {
            "enabled": True,
            "email": "test@example.com",
            "password": "test_password",
            "post_interval": 1800,
            "max_posts_per_day": 10
        },
        "global": {
            "headless": False,
            "timeout": 30,
            "retry_attempts": 3
        }
    }

@pytest.fixture
def mock_task_data():
    """Create mock task data."""
    return [
        {
            "type": "post",
            "platform": "twitter",
            "content": "Test post 1",
            "media": ["test_image.jpg"]
        },
        {
            "type": "comment",
            "platform": "reddit",
            "content": "Test comment",
            "subreddit": "test_subreddit"
        }
    ]

@pytest.fixture
def social_config(mock_config_data):
    """Create a SocialConfig instance with mock data."""
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
        with patch('pathlib.Path.exists', return_value=True):
            config = SocialConfig()
            config.load_config()
            return config

@pytest.fixture
def task_dispatcher(social_config, mock_task_data):
    """Create a TaskDispatcher instance with mock data."""
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_task_data))):
        with patch('pathlib.Path.exists', return_value=True):
            dispatcher = TaskDispatcher(social_config)
            dispatcher.load_tasks()
            return dispatcher

def test_config_dispatcher_integration(social_config, task_dispatcher):
    """Test integration between SocialConfig and TaskDispatcher."""
    # Verify config is loaded correctly
    assert social_config.get("twitter.enabled") is True
    assert social_config.get("twitter.email") == "test@example.com"
    
    # Verify tasks are loaded correctly
    assert len(task_dispatcher.tasks) == 2
    assert task_dispatcher.tasks[0]["platform"] == "twitter"
    assert task_dispatcher.tasks[1]["platform"] == "reddit"
    
    # Test task dispatch with config validation
    def mock_handler(task):
        platform = task["platform"]
        if not social_config.get(f"{platform}.enabled", False):
            return False
        return True
    
    # Twitter task should succeed (enabled in config)
    result = task_dispatcher.dispatch_task(task_dispatcher.tasks[0], mock_handler)
    assert result is True
    assert task_dispatcher.memory_updates["tasks_completed"] == 1
    
    # Reddit task should fail (not enabled in config)
    result = task_dispatcher.dispatch_task(task_dispatcher.tasks[1], mock_handler)
    assert result is False
    assert task_dispatcher.memory_updates["tasks_failed"] == 1

def test_memory_tracking_integration(social_config, task_dispatcher):
    """Test memory tracking across components."""
    # Update config
    social_config.set("twitter.enabled", False)
    assert social_config.memory_updates["last_action"]["action"] == "set"
    
    # Add new task
    new_task = {
        "type": "post",
        "platform": "twitter",
        "content": "New test post"
    }
    task_dispatcher.add_task(new_task)
    assert task_dispatcher.memory_updates["last_action"]["action"] == "add_task"
    
    # Dispatch task
    def mock_handler(task):
        return False
    
    task_dispatcher.dispatch_task(new_task, mock_handler)
    assert task_dispatcher.memory_updates["tasks_failed"] == 1
    assert "Task handler returned False" in str(task_dispatcher.memory_updates["last_error"]["error"])

def test_error_handling_integration(social_config, task_dispatcher):
    """Test error handling across components."""
    # Test config error
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        result = social_config.save_config()
        assert result is False
        assert "Permission denied" in str(social_config.memory_updates["last_error"]["error"])
    
    # Test task error
    def mock_handler(task):
        raise Exception("Task execution failed")
    
    task = task_dispatcher.get_next_task()
    result = task_dispatcher.dispatch_task(task, mock_handler)
    assert result is False
    assert "Task execution failed" in str(task_dispatcher.memory_updates["last_error"]["error"])

def test_logging_integration(social_config, task_dispatcher):
    """Test logging integration across components."""
    # Test config logging
    social_config.set("twitter.enabled", True)
    assert social_config.logger.write_log.called
    
    # Test dispatcher logging
    task = task_dispatcher.get_next_task()
    task_dispatcher.dispatch_task(task, lambda x: True)
    assert task_dispatcher.logger.write_log.called

def test_config_reload_integration(social_config, task_dispatcher):
    """Test config reload and its effect on task processing."""
    # Update config
    new_config = {
        "twitter": {
            "enabled": False,
            "email": "new@example.com",
            "password": "new_password"
        }
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(new_config))):
        social_config.load_config()
    
    # Verify config update
    assert social_config.get("twitter.enabled") is False
    assert social_config.get("twitter.email") == "new@example.com"
    
    # Verify task processing respects new config
    def mock_handler(task):
        platform = task["platform"]
        return social_config.get(f"{platform}.enabled", False)
    
    task = task_dispatcher.get_next_task()
    result = task_dispatcher.dispatch_task(task, mock_handler)
    assert result is False  # Should fail because twitter is now disabled 