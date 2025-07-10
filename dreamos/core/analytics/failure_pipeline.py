import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = Path("runtime/analytics/failure_logs.db")

class FailureAnalyticsPipeline:
    """Centralized failure analytics using SQLite."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS errors(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    error_type TEXT,
                    message TEXT,
                    timestamp TEXT,
                    resolved INTEGER DEFAULT 0,
                    resolution TEXT,
                    resolution_timestamp TEXT
                )
                """
            )
            conn.commit()

    def log_error(self, agent_id: str, error_type: str, message: str) -> int:
        ts = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO errors(agent_id, error_type, message, timestamp, resolved) VALUES(?,?,?,?,0)",
                (agent_id, error_type, message, ts),
            )
            conn.commit()
            error_id = cur.lastrowid
        logger.error(f"Logged error {error_type} from {agent_id}: {message}")
        return error_id

    def mark_resolved(self, error_id: int, resolution: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE errors SET resolved=1, resolution=?, resolution_timestamp=? WHERE id=?",
                (resolution, datetime.now().isoformat(), error_id),
            )
            conn.commit()
        logger.info(f"Resolved error {error_id}: {resolution}")

    def stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT error_type, COUNT(*) FROM errors GROUP BY error_type")
            counts = {row[0]: row[1] for row in cur.fetchall()}
            cur.execute("SELECT COUNT(*) FROM errors WHERE resolved=1")
            resolved = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM errors")
            total = cur.fetchone()[0]
        resolution_rate = (resolved / total * 100) if total else 0.0
        return {
            "counts": counts,
            "total": total,
            "resolved": resolved,
            "resolution_rate": resolution_rate,
        }
