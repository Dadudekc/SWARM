import pytest

# ---------------------------------------------------------------------------
# Active functional tests for `AgentStateManager`                           
# ---------------------------------------------------------------------------

import asyncio
from pathlib import Path
from uuid import uuid4

from dreamos.core.resumer_v2.agent_state_manager import AgentStateManager


# ---------------------------------------------------------------------------
# Fixtures                                                                   
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_state_dir(tmp_path: Path) -> Path:  # noqa: D401
    """Return an *empty* temporary directory that the state-manager can use."""
    return tmp_path


# ---------------------------------------------------------------------------
# Tests                                                                      
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_state_manager_basic(tmp_state_dir: Path) -> None:  # noqa: D401
    """`AgentStateManager` should initialise files, add a task, and clean up."""

    mgr = AgentStateManager(str(tmp_state_dir))

    # After construction the state file must exist and contain an *idle* state.
    state = await mgr.get_state()
    assert state["status"] == "idle"
    assert state["agent_id"] == "default"

    # Add a minimal task and verify it lands in the persisted structure.
    now = "2025-01-01T00:00:00"
    task_payload = {
        "id": str(uuid4()),
        "type": "unit",
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "data": {},
    }
    assert await mgr.add_task(task_payload)

    tasks = await mgr.get_tasks()
    assert "unit" in tasks and len(tasks["unit"]) == 1

    # Clean up artefacts (important on Windows where open handles linger).
    await mgr.cleanup()

# ---------------------------------------------------------------------------
# The legacy stub tests remain skipped until full behaviour is specified.    
# ---------------------------------------------------------------------------
