#!/usr/bin/env python3
import os
import json
import pytest
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Test imports first
def test_imports():
    """Test that all required modules can be imported."""
    try:
        from agent_tools.utils.init_mailbox import AgentMailbox
        assert callable(AgentMailbox)
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")

# Import after test to ensure clean state
from agent_tools.utils.init_mailbox import AgentMailbox

# Setup logger
logger = logging.getLogger("agent_mailbox")

@pytest.fixture
def temp_mailbox_dir(tmp_path):
    """Create a temporary directory for mailbox testing."""
    mailbox_dir = tmp_path / "agent_mailboxes"
    mailbox_dir.mkdir()
    yield str(mailbox_dir)
    # Cleanup happens automatically with tmp_path fixture

@pytest.fixture
def test_agent_id():
    """Test agent ID."""
    return "Test-Agent"

@pytest.fixture
def mailbox(temp_mailbox_dir, test_agent_id):
    """Create a mailbox instance for testing."""
    return AgentMailbox(test_agent_id, temp_mailbox_dir)

def test_get_initial_state(mailbox):
    """Test initial state generation."""
    current_time = datetime.now()
    state = mailbox._get_initial_state(current_time)
    
    # Check structure
    assert "inbox" in state
    assert "status" in state
    assert "devlog" in state
    
    # Check inbox content
    assert state["inbox"]["type"] == "INIT"
    assert state["inbox"]["from"] == "bootstrap"
    assert state["inbox"]["timestamp"] == current_time.isoformat()
    
    # Check status content
    assert state["status"]["agent_id"] == mailbox.agent_id
    assert state["status"]["status"] == "idle"
    assert state["status"]["cycle_count"] == 0
    assert state["status"]["error_count"] == 0
    
    # Check devlog content
    assert mailbox.agent_id in state["devlog"]
    assert "Boot Log" in state["devlog"]
    assert current_time.strftime('%Y-%m-%d') in state["devlog"]

def test_init_mailbox_creates_files(mailbox):
    """Test that initialization creates all required files."""
    mailbox.initialize()
    
    # Check directory exists
    assert mailbox.agent_dir.exists()
    assert mailbox.agent_dir.is_dir()
    
    # Check all files exist
    assert (mailbox.agent_dir / "inbox.json").exists()
    assert (mailbox.agent_dir / "status.json").exists()
    assert (mailbox.agent_dir / "devlog.md").exists()

def test_init_mailbox_file_contents(mailbox):
    """Test that initialized files have correct content."""
    mailbox.initialize()
    
    # Check inbox.json
    with open(mailbox.agent_dir / "inbox.json", "r", encoding='utf-8') as f:
        inbox = json.load(f)
    assert inbox["type"] == "INIT"
    assert inbox["from"] == "bootstrap"
    
    # Check status.json
    with open(mailbox.agent_dir / "status.json", "r", encoding='utf-8') as f:
        status = json.load(f)
    assert status["agent_id"] == mailbox.agent_id
    assert status["status"] == "idle"
    assert status["cycle_count"] == 0

def test_init_mailbox_duplicate(mailbox, capsys):
    """Test that initializing an existing mailbox warns user."""
    # First initialization
    mailbox.initialize()
    
    # Second initialization
    mailbox.initialize()
    
    # Check warning message
    captured = capsys.readouterr()
    assert "already exists" in captured.out
    assert "--reset" in captured.out

def test_reset_mailbox_creates_backup(mailbox):
    """Test that reset creates a backup of existing mailbox."""
    # Initialize mailbox
    mailbox.initialize()
    
    # Modify a file
    with open(mailbox.agent_dir / "status.json", "w", encoding='utf-8') as f:
        json.dump({"modified": True}, f)
    
    # Reset mailbox
    mailbox.reset()
    
    # Check backup exists
    backups = list(mailbox.agent_dir.parent.glob(f"{mailbox.agent_id.lower()}_backup_*"))
    assert len(backups) == 1
    assert backups[0].is_dir()

def test_reset_mailbox_restores_state(mailbox):
    """Test that reset restores all files to initial state."""
    # Initialize mailbox
    mailbox.initialize()
    
    # Modify files
    with open(mailbox.agent_dir / "status.json", "w", encoding='utf-8') as f:
        json.dump({"modified": True}, f)
    with open(mailbox.agent_dir / "inbox.json", "w", encoding='utf-8') as f:
        json.dump({"modified": True}, f)
    with open(mailbox.agent_dir / "devlog.md", "w", encoding='utf-8') as f:
        f.write("Modified content")
    
    # Reset mailbox
    mailbox.reset()
    
    # Check files are restored
    with open(mailbox.agent_dir / "status.json", "r", encoding='utf-8') as f:
        status = json.load(f)
    assert status["agent_id"] == mailbox.agent_id
    assert status["status"] == "idle"
    
    with open(mailbox.agent_dir / "inbox.json", "r", encoding='utf-8') as f:
        inbox = json.load(f)
    assert inbox["type"] == "INIT"
    assert inbox["from"] == "bootstrap"

def test_reset_nonexistent_mailbox(mailbox):
    """Test that reset works on nonexistent mailbox."""
    mailbox.reset()
    
    assert mailbox.agent_dir.exists()
    assert (mailbox.agent_dir / "inbox.json").exists()
    assert (mailbox.agent_dir / "status.json").exists()
    assert (mailbox.agent_dir / "devlog.md").exists()

def test_init_mailbox_invalid_agent_id(temp_mailbox_dir):
    """Test initialization with invalid agent ID."""
    with pytest.raises(ValueError):
        AgentMailbox("", temp_mailbox_dir)
    
    with pytest.raises(ValueError):
        AgentMailbox(None, temp_mailbox_dir)
    
    with pytest.raises(ValueError):
        AgentMailbox("Invalid/Agent/ID", temp_mailbox_dir)
    
    with pytest.raises(ValueError):
        AgentMailbox("Agent*ID", temp_mailbox_dir)

def test_init_mailbox_invalid_directory(test_agent_id, monkeypatch):
    """Test initialization with invalid directory."""
    # Patch Path.mkdir to always raise OSError for this test
    def raise_oserror(*args, **kwargs):
        raise OSError("Invalid directory")
    monkeypatch.setattr("pathlib.Path.mkdir", raise_oserror)
    with pytest.raises(OSError):
        AgentMailbox(test_agent_id, "C:\\invalid\\path\\with\\*chars")
    with pytest.raises(OSError):
        AgentMailbox(test_agent_id, "C:\\invalid\\path\\with\\?chars")

def test_reset_mailbox_permission_error(mailbox, monkeypatch):
    """Test reset behavior when backup fails."""
    # Initialize mailbox
    mailbox.initialize()
    
    # Mock shutil.copytree to raise PermissionError
    def mock_copytree(*args, **kwargs):
        raise PermissionError("Permission denied")
    
    monkeypatch.setattr(shutil, "copytree", mock_copytree)
    
    # Reset should still work even if backup fails
    mailbox.reset()
    
    # Verify mailbox was reset
    with open(mailbox.agent_dir / "status.json", "r", encoding='utf-8') as f:
        status = json.load(f)
    assert status["status"] == "idle"

def test_concurrent_mailbox_operations(mailbox):
    """Test concurrent initialization and reset operations."""
    import threading
    import time
    
    def init_operation():
        mailbox.initialize()
    
    def reset_operation():
        time.sleep(0.1)  # Ensure init starts first
        mailbox.reset()
    
    # Run init and reset concurrently
    init_thread = threading.Thread(target=init_operation)
    reset_thread = threading.Thread(target=reset_operation)
    
    init_thread.start()
    reset_thread.start()
    
    init_thread.join()
    reset_thread.join()
    
    # Verify final state
    assert mailbox.agent_dir.exists()
    
    with open(mailbox.agent_dir / "status.json", "r", encoding='utf-8') as f:
        status = json.load(f)
    assert status["status"] == "idle"

def test_mailbox_file_permissions(mailbox):
    """Test mailbox file permissions."""
    mailbox.initialize()
    
    # Check file permissions
    for file in mailbox.agent_dir.glob("*"):
        assert os.access(file, os.R_OK), f"{file} should be readable"
        assert os.access(file, os.W_OK), f"{file} should be writable"

def test_mailbox_file_encoding(mailbox):
    """Test mailbox file encoding handling."""
    mailbox.initialize()
    
    # Test writing Unicode content
    unicode_content = "Test content with Unicode: 你好世界"
    with open(mailbox.agent_dir / "devlog.md", "w", encoding='utf-8') as f:
        f.write(unicode_content)
    
    # Verify content was written correctly
    with open(mailbox.agent_dir / "devlog.md", "r", encoding='utf-8') as f:
        content = f.read()
    assert content == unicode_content

def test_mailbox_file_corruption(mailbox):
    """Test handling of corrupted mailbox files."""
    mailbox.initialize()
    
    # Corrupt status.json
    with open(mailbox.agent_dir / "status.json", "w", encoding='utf-8') as f:
        f.write("invalid json content")
    
    # Reset should handle corrupted files
    mailbox.reset()
    
    # Verify file was restored
    with open(mailbox.agent_dir / "status.json", "r", encoding='utf-8') as f:
        status = json.load(f)
    assert status["status"] == "idle"

def test_mailbox_directory_cleanup(mailbox):
    """Test mailbox directory cleanup."""
    mailbox.initialize()
    
    # Create some extra files
    extra_file = mailbox.agent_dir / "extra.txt"
    extra_file.write_text("test")
    
    # Reset should clean up extra files
    mailbox.reset()
    assert not extra_file.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
