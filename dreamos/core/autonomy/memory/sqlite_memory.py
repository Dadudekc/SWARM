import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

MEMORY_DB = Path("runtime/agent_memory/memory.db")

class SQLiteMemory:
    """SQLite-backed persistent memory store."""

    def __init__(self, db_path: Path = MEMORY_DB) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memories(
                    agent_id TEXT,
                    key TEXT,
                    value TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(agent_id, key)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots(
                    agent_id TEXT,
                    snapshot TEXT,
                    timestamp TEXT
                )
                """
            )
            conn.commit()

    def store_memory(self, agent_id: str, key: str, value: Any) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "REPLACE INTO memories(agent_id, key, value, updated_at) VALUES(?,?,?,?)",
                (agent_id, key, json.dumps(value), datetime.now().isoformat()),
            )
            conn.commit()
        logger.info(f"Stored memory for {agent_id}: {key}")

    def recall_memory(self, agent_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM memories WHERE agent_id=?", (agent_id,))
            rows = cur.fetchall()
        return {k: json.loads(v) for k, v in rows}

    def inject_memory(self, agent_id: str, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self.store_memory(agent_id, k, v)

    def snapshot(self, agent_id: str) -> None:
        state = json.dumps(self.recall_memory(agent_id))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO snapshots(agent_id, snapshot, timestamp) VALUES(?,?,?)",
                (agent_id, state, datetime.now().isoformat()),
            )
            conn.commit()
        logger.info(f"Snapshot saved for {agent_id}")

