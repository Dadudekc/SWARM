import json
from pathlib import Path
from dreamos.core.ai import dreamscribe as ds_mod
from tools.devlog.ingest_devlogs import ingest_agent_devlog


def _patch_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(ds_mod, "MEMORY_CORPUS_PATH", tmp_path / "memory.json")
    monkeypatch.setattr(ds_mod, "NARRATIVE_THREADS_PATH", tmp_path / "threads")
    monkeypatch.setattr(ds_mod, "INSIGHT_PATTERNS_PATH", tmp_path / "patterns.json")


def test_ingest_agent_devlog(monkeypatch, tmp_path):
    _patch_paths(tmp_path, monkeypatch)
    scribe = ds_mod.Dreamscribe()
    devlog_dir = tmp_path / "agent1"
    devlog_dir.mkdir()
    devlog_file = devlog_dir / "devlog.md"
    devlog_file.write_text("## Task 1\nDid something\n## Task 2\nAnother thing")

    ids = ingest_agent_devlog("agent1", devlog_file, scribe)
    assert len(ids) == 2
    mem = scribe.get_memory(ids[0])
    assert mem["agent_id"] == "agent1"
