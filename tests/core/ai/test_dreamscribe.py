from dreamos.core.ai import dreamscribe as ds_mod


def _patch_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(ds_mod, "MEMORY_CORPUS_PATH", tmp_path / "memory.json")
    monkeypatch.setattr(ds_mod, "NARRATIVE_THREADS_PATH", tmp_path / "threads")
    monkeypatch.setattr(ds_mod, "INSIGHT_PATTERNS_PATH", tmp_path / "patterns.json")


def test_query_memories_filters(monkeypatch, tmp_path):
    _patch_paths(tmp_path, monkeypatch)
    scribe = ds_mod.Dreamscribe()

    scribe.ingest_devlog({"agent_id": "a1", "content": "task complete"})
    scribe.ingest_devlog({"agent_id": "a2", "content": "failure occurred"})

    res = scribe.query_memories(agent_id="a1")
    assert len(res) == 1
    assert res[0]["agent_id"] == "a1"

    res = scribe.query_memories(keyword="failure")
    assert len(res) == 1
    assert res[0]["agent_id"] == "a2"
