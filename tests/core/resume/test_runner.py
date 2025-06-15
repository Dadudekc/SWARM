"""Unit tests for *tools.core.resume.runner.run_resume_sequence*.

These tests monkey-patch *restart_agent* and *send_initial_message* so the
shared runner can be executed without any GUI / pyautogui side-effects.
"""
from __future__ import annotations

from typing import List

import importlib
import types

import pytest

MODULE_PATH = "tools.core.resume.runner"


@pytest.fixture()
def runner_module():
    """Return a freshly re-imported *runner* module so patched symbols are used."""
    mod = importlib.import_module(MODULE_PATH)
    return importlib.reload(mod)


def _install_stubs(monkeypatch, runner, restart_returns: List[bool]):
    """Helper to stub *restart_agent* / *send_initial_message* on *runner*.

    Args:
        monkeypatch: pytest fixture instance.
        runner: Imported *runner* module.
        restart_returns: Sequence of booleans to return for each *restart* call.
    """
    calls = {
        "restart": [],
        "send": [],
    }

    def _fake_restart(agent_name: str):  # noqa: D401
        idx = len(calls["restart"])
        calls["restart"].append(agent_name)
        # Default to last value if list shorter than calls
        ret = restart_returns[idx] if idx < len(restart_returns) else restart_returns[-1]
        return ret

    def _fake_send(agent_name: str, prompt=None, *, delay: float = 0.0):  # noqa: D401, ANN001
        calls["send"].append(agent_name)
        return True

    monkeypatch.setattr(runner, "restart_agent", _fake_restart)
    monkeypatch.setattr(runner, "send_initial_message", _fake_send)
    # Speed up tests no matter what *delay* is
    monkeypatch.setattr(runner, "time", types.SimpleNamespace(sleep=lambda _: None))

    return calls


def test_happy_path_invokes_restart_and_send_for_each_agent(runner_module, monkeypatch):
    agents = ["Agent-1", "Agent-2", "Agent-3"]
    calls = _install_stubs(monkeypatch, runner_module, restart_returns=[True, True, True])

    runner_module.run_resume_sequence(agents, delay=0.0)

    assert calls["restart"] == agents
    assert calls["send"] == agents


def test_send_skipped_when_restart_fails(runner_module, monkeypatch):
    agents = ["Agent-A", "Agent-B", "Agent-C"]
    # Simulate failure for the middle agent only
    calls = _install_stubs(monkeypatch, runner_module, restart_returns=[True, False, True])

    runner_module.run_resume_sequence(agents, delay=0.0)

    # restart must be attempted for all agents
    assert calls["restart"] == agents
    # send_initial_message should be *skipped* for the failed one
    assert calls["send"] == ["Agent-A", "Agent-C"]


def test_run_resume_sequence_monkeypatch(monkeypatch):
    """run_resume_sequence should call helper functions for each agent."""

    monkeypatch.setattr(runner_module, "restart_agent", _fake_restart)
    monkeypatch.setattr(runner_module, "send_initial_message", _fake_send_message)

    agents = ["Agent-1", "Agent-2"]

    # Track post_hook invocations
    post_invocations = {}

    def _post_hook(agent: str, success: bool):  # noqa: D401
        post_invocations[agent] = success

    runner_module.run_resume_sequence(agents, prompt="Hi", delay=0.0, post_hook=_post_hook)

    assert calls["restart"] == agents
    assert calls["send"] == agents
    # post_hook called with success=True for each agent
    assert post_invocations == {agent: True for agent in agents} 