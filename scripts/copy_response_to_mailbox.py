"""Copy latest Cursor response and drop into THEA's mailbox."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import pyperclip

COORDS_FILE = Path("config/cursor_agent_coords.json")
MAILBOX_ROOT = Path("agent_tools/mailbox")
AGENT_ID = "agent-2"
TARGET_AGENT = "thea"


def load_coords(agent: str) -> dict:
    data = json.loads(COORDS_FILE.read_text())
    key = agent.replace("agent", "Agent")
    return data.get(key, {})


def write_mailbox(agent: str, message: dict) -> None:
    inbox = MAILBOX_ROOT / agent / "inbox.json"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    if inbox.exists():
        try:
            payload = json.loads(inbox.read_text())
            if not isinstance(payload, list):
                payload = [payload]
        except Exception:
            payload = []
    else:
        payload = []
    payload.append(message)
    inbox.write_text(json.dumps(payload, indent=2))


def main() -> None:
    coords = load_coords(AGENT_ID)
    if not coords:
        raise SystemExit(f"No coordinates for {AGENT_ID}")
    button = coords.get("copy_button")
    if not button:
        raise SystemExit("Missing copy button coords")

    pyautogui.click(button["x"], button["y"])
    time.sleep(0.5)
    content = pyperclip.paste()

    message = {
        "sender": AGENT_ID,
        "type": "bridge_request",
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    write_mailbox(TARGET_AGENT, message)


if __name__ == "__main__":
    main()
