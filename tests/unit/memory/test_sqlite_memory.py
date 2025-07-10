import tempfile
from dreamos.core.autonomy.memory.sqlite_memory import SQLiteMemory

def test_store_and_recall():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    mem = SQLiteMemory(db_path=tmp.name)
    mem.store_memory("agent", "task", {"step": 1})
    new_mem = SQLiteMemory(db_path=tmp.name)
    data = new_mem.recall_memory("agent")
    assert data["task"] == {"step": 1}
