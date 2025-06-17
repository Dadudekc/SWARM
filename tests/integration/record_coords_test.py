"""Integration stub for *scripts.record_coords*.

Validates that running :pyfunc:`scripts.record_coords.record` updates the
JSON mapping with the monkey-patched coordinates.  The interactive ``input``
call and ``pyautogui`` dependency are stubbed so the test runs headless.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

MODULE = "scripts.record_coords"


class _FakePG:  # minimal stub for *pyautogui*
    def __init__(self, pos: tuple[int, int]):
        self._pos = pos

    def position(self):  # noqa: D401 – mimic pyautogui API
        return self._pos


@pytest.mark.parametrize("coords", [(123, 456), (10, 20)])
def test_record_updates_json(tmp_path: Path, monkeypatch, coords):
    # Patch *pyautogui* before import so module picks up stub
    monkeypatch.setitem(sys.modules, "pyautogui", _FakePG(coords))

    rc = importlib.import_module(MODULE)

    # Use a tmp file for isolated storage
    custom_path = tmp_path / "agent_coords.json"

    # Stub *input* so the call returns instantly
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "")

    # Execute record function (non-interactive)
    rc.record(agent=1, profile="windows", p=custom_path)

    assert custom_path.exists(), "JSON file was not created"
    data = json.loads(custom_path.read_text())
    assert data["windows"]["Agent-1"] == {"x": coords[0], "y": coords[1]} 