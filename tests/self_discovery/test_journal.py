import sqlite3
from pathlib import Path

from self_discovery import journal


def test_calculate_relapse_risk():
    text = "I felt a strong urge and craving today"
    score = journal.calculate_relapse_risk(text)
    assert score > 0


def test_add_entry_and_stats(tmp_path: Path):
    db = tmp_path / "life.db"
    journal.init_db(db)
    journal.add_entry("Feeling ok", "🙂", db)
    stats = journal.get_today_stats(db)
    assert stats["journaled"] is True
