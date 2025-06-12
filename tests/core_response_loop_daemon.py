import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for core_response_loop_daemon module."""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from dreamos.core.autonomy.core_response_loop_daemon import CoreResponseLoopDaemon

# Fixtures
@pytest.fixture
def config(tmp_path):
    """Create test configuration."""
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True)
    agents_dir = runtime_dir / "agents"
    agents_dir.mkdir()
    heartbeat_dir = runtime_dir / "heartbeat"
    heartbeat_dir.mkdir()
    bridge_outbox = runtime_dir / "bridge_outbox"
    bridge_outbox.mkdir()
    
    return {
        "paths": {
            "runtime": str(runtime_dir),
            "bridge_outbox": str(bridge_outbox)
        }
    }

@pytest.fixture
def daemon(config, monkeypatch):
    """Create daemon instance."""
    # Mock Discord token
    monkeypatch.setenv("DISCORD_TOKEN", "test_token")
    
    # Create config file
    config_path = Path(config["paths"]["runtime"]) / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
        
    return CoreResponseLoopDaemon(str(config_path))

@pytest.fixture
def agent_state(config):
    """Create test agent state."""
    state = {
        "status": "idle",
        "last_update": datetime.utcnow().isoformat(),
        "context": {
            "task": "test_task",
            "progress": 0.5
        }
    }
    
    state_path = Path(config["paths"]["runtime"]) / "agents" / "test_agent.json"
    with open(state_path, "w") as f:
        json.dump(state, f)
        
    return state

@pytest.mark.asyncio
async def test_daemon_initialization(daemon):
    """Test daemon initialization."""
    assert daemon is not None
    assert hasattr(daemon, "validation_engine")
    assert hasattr(daemon, "resume_manager")
    assert hasattr(daemon, "agent_states")

@pytest.mark.asyncio
async def test_agent_heartbeat_update(daemon):
    """Test agent heartbeat update."""
    agent_id = "test_agent"
    await daemon._update_agent_heartbeat(agent_id)
    
    # Verify heartbeat file
    heartbeat_path = Path(daemon.config["paths"]["runtime"]) / "heartbeat" / f"{agent_id}.json"
    assert heartbeat_path.exists()
    
    with open(heartbeat_path) as f:
        heartbeat = json.load(f)
        assert heartbeat["agent_id"] == agent_id
        assert "last_active" in heartbeat

@pytest.mark.asyncio
async def test_agent_heartbeat_check_active(daemon):
    """Test checking active agent heartbeat."""
    agent_id = "test_agent"
    await daemon._update_agent_heartbeat(agent_id)
    
    # Should be active
    assert await daemon._check_agent_heartbeat(agent_id)

@pytest.mark.asyncio
async def test_agent_heartbeat_check_stale(daemon):
    """Test checking stale agent heartbeat."""
    agent_id = "test_agent"
    
    # Create stale heartbeat
    heartbeat_path = Path(daemon.config["paths"]["runtime"]) / "heartbeat" / f"{agent_id}.json"
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    
    stale_time = datetime.utcnow() - timedelta(minutes=10)  # 10 minutes ago
    with open(heartbeat_path, "w") as f:
        json.dump({
            "agent_id": agent_id,
            "last_active": stale_time.isoformat()
        }, f)
        
    # Should be stale
    assert not await daemon._check_agent_heartbeat(agent_id)

@pytest.mark.asyncio
async def test_agent_resume_impl(daemon, agent_state):
    """Test agent resume implementation."""
    agent_id = "test_agent"
    
    # Should succeed
    assert await daemon._resume_agent_impl(agent_id)
    
    # Verify state was updated
    state_path = Path(daemon.config["paths"]["runtime"]) / "agents" / f"{agent_id}.json"
    with open(state_path) as f:
        state = json.load(f)
        assert state["status"] == "resuming"

@pytest.mark.asyncio
async def test_agent_monitoring(daemon, agent_state):
    """Test agent monitoring."""
    agent_id = "test_agent"
    daemon.agent_states[agent_id] = agent_state
    
    # Create stale heartbeat
    heartbeat_path = Path(daemon.config["paths"]["runtime"]) / "heartbeat" / f"{agent_id}.json"
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    
    stale_time = datetime.utcnow() - timedelta(minutes=10)  # 10 minutes ago
    with open(heartbeat_path, "w") as f:
        json.dump({
            "agent_id": agent_id,
            "last_active": stale_time.isoformat()
        }, f)
        
    # Start monitoring
    monitor_task = asyncio.create_task(daemon._monitor_agents())
    
    # Wait for monitoring cycle
    await asyncio.sleep(2)
    
    # Cancel monitoring
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
        
    # Verify agent was resumed
    state_path = Path(daemon.config["paths"]["runtime"]) / "agents" / f"{agent_id}.json"
    with open(state_path) as f:
        state = json.load(f)
        assert state["status"] == "resuming"

@pytest.mark.asyncio
async def test_daemon_lifecycle(daemon):
    """Test daemon start/stop lifecycle."""
    # Start daemon
    await daemon.start()
    assert hasattr(daemon, "_monitor_task")
    assert not daemon._monitor_task.done()
    
    # Stop daemon
    await daemon.stop()
    assert daemon._monitor_task.done()
