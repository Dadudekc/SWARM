#!/usr/bin/env python3
"""AutoPitch Machine
-------------------
Scrape devlog entries into social media pitches.
"""

import argparse
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import requests

from PIL import Image, ImageDraw, ImageFont

from dreamos.core.ai.chatgpt_bridge import ChatGPTBridge


_DEF_FONT = ImageFont.load_default()


def parse_devlog(devlog_path: Path) -> List[Dict[str, str]]:
    """Extract entries from a devlog markdown file."""
    entries: List[Dict[str, str]] = []
    if not devlog_path.exists():
        return entries
    heading: Optional[str] = None
    lines: List[str] = []
    with devlog_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                if heading:
                    entries.append({"heading": heading, "content": "\n".join(lines).strip()})
                heading = line[3:].strip()
                lines = []
            else:
                lines.append(line.rstrip())
    if heading:
        entries.append({"heading": heading, "content": "\n".join(lines).strip()})
    return entries


async def generate_caption(bridge: ChatGPTBridge, text: str) -> str:
    """Generate a short caption summarizing the text."""
    messages = [
        bridge.format_system_message(
            "You turn devlog snippets into catchy social media captions under 280 characters."),
        bridge.format_user_message(text)
    ]
    resp = await bridge.chat(messages, temperature=0.5, max_tokens=60)
    caption = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return caption


def create_visual(text: str, screenshot: Optional[Path], out_path: Path) -> Path:
    """Overlay caption text on screenshot or placeholder image."""
    img: Image.Image
    if screenshot and screenshot.exists():
        img = Image.open(screenshot).convert("RGB")
    else:
        img = Image.new("RGB", (800, 450), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)
    margin = 20
    max_width = img.width - 2 * margin
    wrapped = []
    for word in text.split():
        if not wrapped:
            wrapped.append(word)
            continue
        line = wrapped[-1] + " " + word
        w, _ = draw.textsize(line, font=_DEF_FONT)
        if w <= max_width:
            wrapped[-1] = line
        else:
            wrapped.append(word)
    y = img.height - margin - len(wrapped) * 12
    for line in wrapped:
        w, h = draw.textsize(line, font=_DEF_FONT)
        draw.text(((img.width - w) // 2, y), line, fill=(255, 255, 255), font=_DEF_FONT)
        y += h
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def send_to_discord(webhook: str, caption: str, image: Path) -> bool:
    """Send caption and image to Discord via webhook."""
    embed = {
        "title": "AutoPitch",
        "description": caption,
        "color": 0x00FF00,
        "timestamp": datetime.utcnow().isoformat()
    }
    files = {
        'file': (image.name, image.open('rb'), 'image/png')
    }
    payload = {"embeds": [embed]}
    try:
        response = requests.post(webhook, data={"payload_json": requests.utils.json.dumps(payload)}, files=files, timeout=10)
        response.raise_for_status()
        return True
    except Exception:
        return False


async def main() -> None:
    ap = argparse.ArgumentParser(description="Generate social media pitches from devlog entries")
    ap.add_argument("--devlog", type=Path, default=Path("data/devlog.md"))
    ap.add_argument("--out", type=Path, default=Path("runtime/pitches"))
    ap.add_argument("--webhook", type=str, default=os.getenv("DISCORD_WEBHOOK_URL"))
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--screenshot", type=Path, default=None, help="Optional screenshot image")
    args = ap.parse_args()

    entries = parse_devlog(args.devlog)
    if not entries:
        print("No devlog entries found")
        return
    latest = entries[-args.limit:]

    async with ChatGPTBridge() as bridge:
        for idx, entry in enumerate(latest, 1):
            caption = await generate_caption(bridge, f"{entry['heading']}\n{entry['content']}")
            image_path = create_visual(caption, args.screenshot, args.out / f"pitch_{idx}.png")
            if args.webhook:
                send_to_discord(args.webhook, caption, image_path)
            print(f"Generated pitch: {caption}")


if __name__ == "__main__":
    asyncio.run(main())
