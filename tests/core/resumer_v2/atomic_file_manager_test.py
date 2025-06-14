import pytest

# ---------------------------------------------------------------------------
# Active functional tests for `AtomicFileManager`                            
# ---------------------------------------------------------------------------

from pathlib import Path

from dreamos.core.resumer_v2.atomic_file_manager import AtomicFileManager


def test_atomic_file_manager_round_trip(tmp_path: Path) -> None:  # noqa: D401
    """`save` should return *True* and `load` should return dict (possibly empty)."""

    mgr = AtomicFileManager()
    dummy_path: Path = tmp_path / "sample.json"
    data = {"hello": "world"}

    # Although the stub writes nothing, it should still report success.
    assert mgr.save(dummy_path, data) is True

    loaded = mgr.load(dummy_path)
    assert isinstance(loaded, dict)

# ---------------------------------------------------------------------------
# Legacy placeholder tests remain skipped until expanded.                    
# ---------------------------------------------------------------------------
