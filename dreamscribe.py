"""Digital Dreamscape narrative processor."""

from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from dreamos.core.ai.dreamscribe import Dreamscribe
from dreamos.social.social_formatter import SocialFormatter
from dreamos.social.discord_webhooks import send_discord_message
from tools.devlog.devlog_pitcher import parse_devlog
from dreamos.core.utils.logging_utils import get_logger

LOGGER = get_logger(__name__)
LOG_PATH = Path("runtime/dreamscape_log.jsonl")
DEVLOG_ROOT = Path("runtime/devlog/agents")
LORE_PATH = Path(".memory/lore.jsonl")


def _extract_latest(devlog_path: Path) -> Optional[Dict[str, str]]:
    entries = parse_devlog(devlog_path)
    if not entries:
        return None
    latest = entries[-1]
    match = re.match(r"(?P<task>.+?) at (?P<ts>.+)", latest["heading"], re.I)
    if match:
        task = match.group("task")
        timestamp = match.group("ts")
    else:
        task = latest["heading"]
        timestamp = datetime.now().isoformat()
    return {
        "task": task,
        "timestamp": timestamp,
        "content": latest["content"],
    }


def _sentiment(text: str) -> str:
    lower = text.lower()
    positives = ["success", "completed", "good", "great", "done"]
    negatives = ["fail", "error", "bad", "issue", "problem"]
    if any(p in lower for p in positives):
        return "positive"
    if any(n in lower for n in negatives):
        return "negative"
    return "neutral"


def _append_event(event: Dict[str, str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _append_lore(record: Dict[str, str]) -> None:
    """Persist narrative fragments for long-term lore."""
    LORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LORE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def process_devlog(agent_id: str, devlog_path: Path, scribe: Dreamscribe) -> None:
    entry = _extract_latest(devlog_path)
    if not entry:
        return
    event = {
        "agent": agent_id,
        "timestamp": entry["timestamp"],
        "task": entry["task"],
        "content": entry["content"],
        "sentiment": _sentiment(entry["content"]),
    }
    _append_event(event)
    lesson = (
        "success" if event["sentiment"] == "positive" else
        "needs improvement" if event["sentiment"] == "negative" else
        "observation"
    )
    _append_lore({"event": event["task"], "agent": agent_id, "lesson": lesson})
    scribe.ingest_devlog({
        "agent_id": agent_id,
        "content": entry["content"],
        "context": {"task": entry["task"], "sentiment": event["sentiment"]},
    })
    formatter = SocialFormatter()
    message = formatter.format_post("discord", {
        "title": entry["task"],
        "what": entry["content"],
        "insight": f"sentiment: {event['sentiment']}"
    })
    send_discord_message(message, channel=1)
    LOGGER.info("Dispatched dream event for %s", agent_id)


def get_recent_events(agent_id: str, limit: int = 5) -> list[Dict[str, str]]:
    if not LOG_PATH.exists():
        return []
    events = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("agent") == agent_id:
                    events.append(obj)
            except json.JSONDecodeError:
                continue
    return events[-limit:]


def main() -> None:
    scribe = Dreamscribe()
    if not DEVLOG_ROOT.exists():
        LOGGER.warning("No devlog directory found: %s", DEVLOG_ROOT)
        return
    for devlog in DEVLOG_ROOT.glob("agent*/devlog.md"):
        process_devlog(devlog.parent.name, devlog, scribe)


if __name__ == "__main__":
    main()
