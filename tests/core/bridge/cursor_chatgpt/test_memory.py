import json
from pathlib import Path

from tools.core.bridge.cursor_chatgpt.memory import AletheiaPromptManager, FeedbackEngine


def test_merge_memory_updates(tmp_path):
    mem_file = tmp_path / "mem.json"
    mgr = AletheiaPromptManager(memory_file=str(mem_file))
    mgr.memory_state["data"] = {"names": ["alice"], "count": 1}
    mgr._save_memory = lambda: None  # no disk write

    mgr._merge_memory_updates({"names": ["bob"], "count": 2})

    assert mgr.memory_state["data"]["names"] == ["alice", "bob"]
    assert mgr.memory_state["data"]["count"] == 2


def test_feedback_engine_save_async(tmp_path):
    mem_file = tmp_path / "mem.json"
    engine = FeedbackEngine(memory_file=str(mem_file))

    called = []

    class DummyExecutor:
        def submit(self, fn):
            called.append(True)
            fn()

    engine._executor = DummyExecutor()

    engine.save_memory_async()
    assert called
    assert mem_file.exists()

