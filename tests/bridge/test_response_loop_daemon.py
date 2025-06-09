"""Tests for response loop daemon."""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from bridge.response_loop_daemon import ResponseLoopDaemon
import shutil
import pathlib
from bridge.handlers.response import process_response_file, send_to_chatgpt

@pytest.fixture
def config_path(tmp_path):
    """Create test config file."""
    config = {
        "agent_id": "test-agent",
        "paths": {
            "agent_mailbox": str(tmp_path / "mailbox"),
            "archive": str(tmp_path / "archive"),
            "failed": str(tmp_path / "failed"),
            "validated": str(tmp_path / "validated"),
            "bridge_outbox": str(tmp_path / "outbox"),
            "runtime": str(tmp_path / "runtime")
        },
        "chatgpt": {
            "config_path": str(tmp_path / "chatgpt_config.json"),
            "response_wait": 5
        }
    }
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    # Create all required directories
    for key in ["mailbox", "archive", "failed", "validated", "outbox", "runtime"]:
        dir_path = tmp_path / key
        dir_path.mkdir(parents=True, exist_ok=True)
    # Create minimal chatgpt_config.json
    chatgpt_config_file = tmp_path / "chatgpt_config.json"
    state_file = tmp_path / "state.json"
    with open(chatgpt_config_file, 'w') as f:
        json.dump({
            "browser": {"type": "dummy", "url": "http://localhost"},
            "state": {"state_file": str(state_file)}
        }, f)
    return str(config_file)

@pytest.fixture
def daemon(config_path):
    """Create daemon instance."""
    return ResponseLoopDaemon(config_path)

@pytest.fixture
def sample_response(tmp_path):
    """Create sample response file."""
    response = {
        "message_id": "test-123",
        "content": "Test response",
        "context": "test",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    response_file = tmp_path / "mailbox" / "test-agent.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, 'w') as f:
        json.dump(response, f)
    return response_file

@pytest.fixture
def temp_template_dir(tmp_path):
    """Create a temporary prompt_templates dir with a minimal response_prompt.j2."""
    template_dir = tmp_path / "prompt_templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "response_prompt.j2"
    with open(template_file, 'w') as f:
        f.write("Prompt for agent {{ agent_id }}: {{ response.content }}")
    return str(template_dir)

@pytest.fixture(autouse=True)
def patch_prompt_processor(monkeypatch, temp_template_dir):
    """Patch PromptProcessor to use the temp template dir for all tests."""
    from bridge import processors
    monkeypatch.setattr(processors.prompt, "PromptProcessor", lambda *_: processors.prompt.PromptProcessor(temp_template_dir))

@pytest.mark.asyncio
async def test_initialization(daemon, config_path):
    """Test daemon initialization."""
    assert daemon.config["agent_id"] == "test-agent"
    assert isinstance(daemon.agent_mailbox, Path)
    assert isinstance(daemon.archive_dir, Path)
    assert isinstance(daemon.failed_dir, Path)
    assert isinstance(daemon.validated_dir, Path)

@pytest.mark.asyncio
async def test_start_stop(daemon):
    """Test daemon start/stop."""
    await daemon.start()
    assert daemon.running is True
    # Patch driver to avoid AttributeError
    daemon.bridge.driver = type('DummyDriver', (), {'quit': lambda self: None})()
    await daemon.stop()
    assert daemon.running is False

@pytest.mark.asyncio
async def test_process_response_file(daemon, sample_response):
    """Test response file processing."""
    with patch("bridge.handlers.response.send_to_chatgpt", return_value=True):
        await process_response_file(daemon, sample_response)
        # Check file was moved to archive
        assert not sample_response.exists()
        assert (daemon.archive_dir / sample_response.name).exists()

@pytest.mark.asyncio
async def test_process_response_file_failure(daemon, sample_response, monkeypatch):
    """Test response file processing failure."""
    # Patch extract_agent_id_from_file to return None to simulate failure
    monkeypatch.setattr("dreamos.core.autonomy.utils.response_utils.extract_agent_id_from_file", lambda _: None)
    with patch("bridge.handlers.response.send_to_chatgpt", return_value=False):
        await process_response_file(daemon, sample_response)
        # The file should remain if agent_id is not found
        assert sample_response.exists()

@pytest.mark.asyncio
async def test_send_to_chatgpt(daemon, tmp_path, monkeypatch):
    """Test sending prompt to ChatGPT."""
    # Patch validator to always return True
    monkeypatch.setattr(daemon.validator, "validate_response", lambda _: True)
    validated_path = daemon.validated_dir / "agent-test-agent.json"
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    with open(validated_path, 'w') as f:
        json.dump({"valid": True}, f)
    prompt = {
        "text": "Test prompt",
        "metadata": {
            "agent_id": "test-agent",
            "context": "test"
        }
    }
    # Patch Path.exists to return True for the validated file
    orig_exists = pathlib.Path.exists
    def fake_exists(self):
        if str(self) == str(validated_path):
            return True
        return orig_exists(self)
    monkeypatch.setattr(pathlib.Path, "exists", fake_exists)
    success = await send_to_chatgpt(daemon, prompt, "test-agent")
    assert success is True
    outbox_path = Path(daemon.config["paths"]["bridge_outbox"]) / "agent-test-agent.json"
    assert outbox_path.exists() 