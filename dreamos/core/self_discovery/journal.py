"""Journal utilities for Victor's self-discovery suite."""

from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path("data/life_os.db")
RISK_KEYWORDS = [
    "craving",
    "relapse",
    "bored",
    "urge",
    "lonely",
    "anxious",
    "depressed",
    "stress",
    "trigger",
    "temptation",
    "sad",
]

logger = logging.getLogger(__name__)


def init_db(db_path: Path = DB_PATH) -> None:
    """Ensure required tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS journal_entries("
            "date TEXT PRIMARY KEY, entry TEXT, emotion TEXT, relapse_score REAL)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS coding_sessions("
            "timestamp TEXT, notes TEXT)"
        )
        conn.commit()


def calculate_relapse_risk(text: str, keywords: List[str] | None = None) -> float:
    """Simple keyword based relapse risk score."""
    if keywords is None:
        keywords = RISK_KEYWORDS
    text_lower = text.lower()
    score = sum(text_lower.count(word) for word in keywords)
    return float(score)


def add_entry(entry: str, emotion: str, db_path: Path = DB_PATH) -> None:
    """Add or update today's journal entry."""
    init_db(db_path)
    score = calculate_relapse_risk(entry)
    today = date.today().isoformat()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO journal_entries(date, entry, emotion, relapse_score)"
            " VALUES(?,?,?,?)",
            (today, entry, emotion, score),
        )
        conn.commit()
        logger.info("Saved journal entry for %s with score %.2f", today, score)


def log_coding_session(notes: str, db_path: Path = DB_PATH) -> None:
    """Record a coding session."""
    init_db(db_path)
    timestamp = datetime.now().isoformat()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO coding_sessions(timestamp, notes) VALUES(?,?)",
            (timestamp, notes),
        )
        conn.commit()
        logger.info("Logged coding session at %s", timestamp)


def get_today_stats(db_path: Path = DB_PATH) -> Dict[str, bool]:
    """Return booleans indicating whether activities were completed today."""
    init_db(db_path)
    today = date.today().isoformat()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM journal_entries WHERE date=?", (today,))
        journaled = cur.fetchone() is not None
        try:
            cur.execute("SELECT 1 FROM trades WHERE date(timestamp)=?", (today,))
            traded = cur.fetchone() is not None
        except sqlite3.OperationalError:
            traded = False
        try:
            cur.execute("SELECT 1 FROM coding_sessions WHERE date(timestamp)=?", (today,))
            coded = cur.fetchone() is not None
        except sqlite3.OperationalError:
            coded = False
    return {"journaled": journaled, "traded": traded, "coded": coded}


class Journal:
    """Journal class for managing self-discovery entries."""
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def add_entry(self, entry: str, emotion: str) -> None:
        """Add or update today's journal entry."""
        add_entry(entry, emotion, self.db_path)

    def log_coding_session(self, notes: str) -> None:
        """Record a coding session."""
        log_coding_session(notes, self.db_path)

    def get_today_stats(self) -> Dict[str, bool]:
        """Return booleans indicating whether activities were completed today."""
        return get_today_stats(self.db_path)

    def calculate_relapse_risk(self, text: str, keywords: Optional[List[str]] = None) -> float:
        """Calculate relapse risk score for text."""
        return calculate_relapse_risk(text, keywords)
