import pytest

# ---------------------------------------------------------------------------
# Active functional tests for `QuantumAgentResumer`                           
# ---------------------------------------------------------------------------

import asyncio
from pathlib import Path

from dreamos.core.resumer_v2.quantum_agent_resumer import QuantumAgentResumer


@pytest.mark.asyncio
async def test_quantum_agent_resumer_start_stop(tmp_path: Path) -> None:  # noqa: D401
    """Resumer should start, increment a cycle, and stop cleanly."""

    resumer = QuantumAgentResumer(str(tmp_path))

    # Start the resumer – this spawns a background health-check.
    await resumer.start()

    # Perform a quick mutation so we hit some of the code-paths.
    assert await resumer.increment_cycle() is True

    # Now stop and ensure the _running flag is cleared.
    await resumer.stop()
    assert resumer._running is False

# ---------------------------------------------------------------------------
# Legacy placeholder tests remain skipped until expanded.                    
# ---------------------------------------------------------------------------
