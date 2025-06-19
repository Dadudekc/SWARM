"""Simple mailbox bridge loop for THEA."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pyautogui

from dreamos.core.ai.chatgpt_bridge import ChatGPTBridge

COORDS_FILE = Path("config/cursor_agent_coords.json")
MAILBOX_ROOT = Path("agent_tools/mailbox")
THEA_ID = "thea"
POLL_INTERVAL = 5  # seconds


def load_coords(agent: str) -> dict:
    data = json.loads(COORDS_FILE.read_text())
    key = agent.replace("agent", "Agent")
    return data.get(key, {})


def read_inbox(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else [data]
    except Exception:
        return []


def write_inbox(path: Path, messages: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(messages, indent=2))


async def process_message(bridge: ChatGPTBridge, message: dict) -> None:
    origin_agent = message.get("sender") or "agent-2"
    content = message.get("content", "")
    response = await bridge.chat([
        {"role": "user", "content": content}
    ])
    text = response["choices"][0]["message"]["content"] if response else ""

    reply = {
        "sender": THEA_ID,
        "type": "bridge_reply",
        "content": text,
        "timestamp": datetime.utcnow().isoformat(),
    }
    target_inbox = MAILBOX_ROOT / origin_agent / "inbox.json"
    existing = read_inbox(target_inbox)
    existing.append(reply)
    write_inbox(target_inbox, existing)

    coords = load_coords(origin_agent)
    if coords:
        box = coords.get("input_box")
        if box:
            pyautogui.click(box["x"], box["y"])
            pyautogui.write(text, interval=0.01)


async def bridge_loop() -> None:
    inbox_path = MAILBOX_ROOT / THEA_ID / "inbox.json"
    async with ChatGPTBridge() as bridge:
        while True:
            messages = read_inbox(inbox_path)
            if messages:
                write_inbox(inbox_path, [])
                for msg in messages:
                    await process_message(bridge, msg)
            await asyncio.sleep(POLL_INTERVAL)


def main() -> None:
    asyncio.run(bridge_loop())


if __name__ == "__main__":
    main()
