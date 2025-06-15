"""Shared resume runner logic (Patch-2).

This small utility holds the loop that every *resume* entry-point uses so we
avoid behavioural drift between scripts.
"""
from __future__ import annotations

import inspect
import logging
import time
from typing import Callable, List, Optional

from tools.core.resume.agent_restart import restart_agent, send_initial_message

logger = logging.getLogger(__name__)

__all__: list[str] = [
    "run_resume_sequence",
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_resume_sequence(
    agents: List[str],
    *,
    prompt: Optional[str] = None,
    delay: float = 2.0,
    pre_hook: Optional[Callable[[str], None]] = None,
    post_hook: Optional[Callable[[str, bool], None]] = None,
) -> None:
    """Restart *agents* and send *prompt* using shared low-level helpers.

    Args:
        agents: Ordered list of agent identifiers (e.g. ``Agent-1``).
        prompt: Optional custom prompt string passed to
            :pyfunc:`send_initial_message`.  *None* keeps default.
        delay: Seconds between major UI actions.
        pre_hook: Callback executed **before** restarting each agent.
            Signature: ``(agent_name: str) -> None``.
        post_hook: Callback executed **after** the message is sent (or fails).
            Signature: ``(agent_name: str, success: bool) -> None``.
    """

    # Be defensive about hooks so wrappers can pass in functions with fewer
    # positional parameters (e.g. for backwards-compatibility).
    pre_arity = _hook_arity(pre_hook)
    post_arity = _hook_arity(post_hook)

    for agent in agents:
        if pre_hook:
            _safe_invoke(pre_hook, pre_arity, agent)

        restart_ok = restart_agent(agent)
        if not restart_ok:
            logger.error("Failed to restart %s – skipping message", agent)
            if post_hook:
                _safe_invoke(post_hook, post_arity, agent, False)
            time.sleep(delay)
            continue

        time.sleep(delay)

        msg_ok = send_initial_message(agent, prompt=prompt, delay=delay)
        overall_success = restart_ok and msg_ok

        if post_hook:
            _safe_invoke(post_hook, post_arity, agent, overall_success)

        time.sleep(delay)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hook_arity(fn):  # noqa: ANN001
    """Return number of positional args the hook *fn* accepts (0 if None)."""
    if fn is None:
        return 0
    return len(inspect.signature(fn).parameters)


def _safe_invoke(fn, arity: int, agent: str, success: bool | None = None):  # noqa: ANN001
    """Invoke *fn* with the right number of positional parameters."""
    try:
        if arity == 1:
            fn(agent)  # type: ignore[misc]
        elif arity >= 2:
            fn(agent, success)  # type: ignore[misc]
    except Exception as exc:  # pragma: no cover – hook error should not kill loop
        logger.warning("Hook %s raised: %s", fn, exc) 