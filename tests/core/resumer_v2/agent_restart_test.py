"""Unit-tests for *tools.core.resume.agent_restart*.

The real implementation uses **pyautogui** to control a live browser UI, which
isn't available in the test runner.  These tests monkey-patch ``pyautogui`` with
an in-memory stub so we can assert that the correct calls (move, click, write,
press, hotkey) are issued for *Agent-1* … *Agent-4* based on coordinates loaded
from ``cursor_agent_coords.json``.
"""
from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from typing import Dict

import pytest

MODULE_PATH = "tools.core.resume.agent_restart"


class _FakePG(SimpleNamespace):
    """Collects calls to pyautogui functions during a test session."""

    def __init__(self) -> None:
        super().__init__()
        self._calls: list[tuple[str, tuple, dict]] = []

        # Create simple recorders for all API methods we use
        for name in ("moveTo", "click", "write", "press", "hotkey"):
            setattr(self, name, self._make_recorder(name))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        self._calls.clear()

    # internals --------------------------------------------------------
    def _make_recorder(self, name: str):
        def _recorder(*args, **kwargs):  # noqa: ANN001 – generic stub
            self._calls.append((name, args, kwargs))
        return _recorder

    # convenience properties ------------------------------------------
    @property
    def moves(self):
        return [c for c in self._calls if c[0] == "moveTo"]

    @property
    def writes(self):
        return [c for c in self._calls if c[0] == "write"]


@pytest.fixture()
def patched_agent_restart(monkeypatch):
    """Import *agent_restart* with a stubbed *pyautogui* module.

    Returns the re-imported module instance *and* the stub so tests can
    inspect its recorded calls.
    """
    fake_pg = _FakePG()

    # Inject into *sys.modules* **before** import so the module picks it up.
    monkeypatch.setitem(sys.modules, "pyautogui", fake_pg)

    # (Re)load module so the patched pyautogui is used.
    ar = importlib.import_module(MODULE_PATH)
    ar = importlib.reload(ar)

    return ar, fake_pg


@pytest.fixture()
def sample_coords() -> Dict[str, Dict[str, Dict[str, int]]]:
    """Return minimal coordinate mapping for four agents."""
    return {
        "Agent-1": {
            "initial_spot": {"x": 10, "y": 10},
            "input_box_initial": {"x": 15, "y": 20},
        },
        "Agent-2": {
            "initial_spot": {"x": 30, "y": 10},
            "input_box_initial": {"x": 35, "y": 20},
        },
        "Agent-3": {
            "initial_spot": {"x": 50, "y": 10},
            "input_box_initial": {"x": 55, "y": 20},
        },
        "Agent-4": {
            "initial_spot": {"x": 70, "y": 10},
            "input_box_initial": {"x": 75, "y": 20},
        },
    }


@pytest.mark.parametrize("agent_id", ["Agent-1", "Agent-2", "Agent-3", "Agent-4"])
def test_send_initial_message_dispatches_correct_pyautogui_calls(
    patched_agent_restart, sample_coords, monkeypatch, agent_id
):
    ar, pg = patched_agent_restart

    # Monkey-patch *load_coordinates* so no file-io is needed
    monkeypatch.setattr(ar, "load_coordinates", lambda: sample_coords)

    pg.reset()
    ok = ar.send_initial_message(agent_id)
    assert ok, "send_initial_message() should return True"

    # Validate first moveTo uses coordinates from sample mapping
    assert pg.moves, "pyautogui.moveTo() was never called"
    first_move = pg.moves[0]
    exp_pos = sample_coords[agent_id]["input_box_initial"]
    assert first_move[1] == (exp_pos["x"], exp_pos["y"])

    # Validate message content contains the agent-name
    assert pg.writes, "pyautogui.write() was never called"
    assert agent_id in pg.writes[0][1][0] 