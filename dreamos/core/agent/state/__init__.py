"""dreamos.core.agent.state – Agent State subsystem.

The original Agent-State implementation was moved during the 2024 refactor but
several parts of the code-base (and many tests) still import from this
namespace.  Until we port all references, we expose lightweight shim classes so
imports succeed and the test-suite can run.

NOTE: These stubs are *temporary*.  Any production code that relies on them
should be updated to import real implementations from their new locations.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

__all__ = [
    "AgentState",
    "AgentStateManager",
    "QuantumAgentResumer",
    "AgentStateSchema",
]


class _Stub(SimpleNamespace):  # pylint: disable=too-few-public-methods
    """Base class for all placeholder shims."""

    def __getattr__(self, item: str) -> Any:  # noqa: D401
        raise NotImplementedError(
            "Stub class reached: the real implementation was not migrated yet."
        )


class AgentState(_Stub):
    """Placeholder for the real `AgentState` model."""


class AgentStateManager(_Stub):
    """Placeholder for the real `AgentStateManager`."""


class QuantumAgentResumer(_Stub):
    """Placeholder for the real `QuantumAgentResumer`."""


# Alias for backward-compatibility where a Pydantic schema was expected.
AgentStateSchema = AgentState

# Register aliases in `sys.modules` so `from dreamos.core.agent.state.agent_state` works.
sys.modules.setdefault(
    "dreamos.core.agent.state.agent_state", sys.modules[__name__]
) 