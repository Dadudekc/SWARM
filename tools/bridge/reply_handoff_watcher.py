"""Reply → Agent-Resume Watcher
================================
Continuously watches the *ChatCycleController* outbox directory and, for every
new ChatGPT reply file, injects a **resume trigger** message into the
corresponding agent inbox and optionally calls the existing drift-detector
resume helper.

This bridges the gap between the Cursor browser-automation bridge and the
Dream.OS agent loop.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Set

# ---------------------------------------------------------------------------
# Configuration ----------------------------------------------------------------
# ---------------------------------------------------------------------------

OUTBOX_DIR = Path("runtime/bridge_outbox")
INBOX_TEMPLATE = Path("data/agent_{agent_id}/inbox.json")
POLL_INTERVAL = 3  # seconds

logger = logging.getLogger("reply_handoff")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------------------------------------------------------
# Helper functions -----------------------------------------------------------
# ---------------------------------------------------------------------------

def extract_agent_id(file_path: Path) -> str:
    """Infer the *agent_id* from the outbox path.

    Outbox pattern (see ChatCycleController._save_response)::
        runtime/bridge_outbox/<agent_id>/<prompt_name>/<file.txt>
    """
    try:
        # Path structure: .../bridge_outbox/<agent>/<prompt>/<file>
        return file_path.parents[1].name  # one level up from prompt dir
    except IndexError:
        raise ValueError(f"Unexpected outbox path structure: {file_path}")


def build_resume_message(content: str) -> dict:
    """Return a JSON-serialisable resume trigger envelope."""
    return {
        "type": "resume_trigger",
        "from_agent": "chatgpt_bridge",
        "content": content.strip(),
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "source": "reply_handoff_watcher",
            "tags": ["chatgpt_reply", "resume"]
        },
    }


async def write_inbox(agent_id: str, message: dict) -> None:
    """Append *message* to the agent inbox (creates file / dir if needed)."""
    # Build e.g. data/agent_agent-1/inbox.json so that each agent has its own mailbox
    inbox_path = Path(f"data/agent_{agent_id}/inbox.json")
    inbox_path.parent.mkdir(parents=True, exist_ok=True)

    if inbox_path.exists():
        try:
            data = json.loads(inbox_path.read_text())
            if isinstance(data, list):
                data.append(message)
            else:  # legacy single-object schema -> convert
                data = [data, message]
        except Exception:
            data = [message]
    else:
        data = [message]

    inbox_path.write_text(json.dumps(data, indent=2))
    logger.info("📨 Delivered reply to inbox | agent=%s | path=%s", agent_id, inbox_path)


# ---------------------------------------------------------------------------
# Main watcher loop ----------------------------------------------------------
# ---------------------------------------------------------------------------

async def watch_outbox() -> None:
    processed: Set[Path] = set()

    # Pre-populate processed with existing files so we don't re-inject on start
    for file in OUTBOX_DIR.rglob("*.txt"):
        processed.add(file.resolve())

    logger.info("🛰️  Reply-handoff watcher started | dir=%s", OUTBOX_DIR)

    while True:
        try:
            for file in OUTBOX_DIR.rglob("*.txt"):
                real = file.resolve()
                if real in processed:
                    continue

                agent_id = extract_agent_id(real)
                content = real.read_text(encoding="utf-8")
                await write_inbox(agent_id, build_resume_message(content))
                processed.add(real)
        except Exception as exc:
            logger.exception("Watcher error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)


def main() -> None:
    try:
        asyncio.run(watch_outbox())
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        sys.exit(0)


if __name__ == "__main__":
    main() 