import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Optional

from dreamos.core.bridge.chatgpt.bridge import ChatGPTBridge


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


async def generate_pitch(devlog_path: Path, limit: int) -> str:
    """Generate product pitches from a devlog file."""
    entries = parse_devlog(devlog_path)
    if not entries:
        return "No devlog entries found."
    latest = entries[-limit:]
    async with ChatGPTBridge() as bridge:
        output_lines: List[str] = []
        for entry in latest:
            messages = [
                bridge.format_system_message(
                    "You are a product marketing expert. Summarize the devlog snippet into a short pitch for customers."),
                bridge.format_user_message(f"{entry['heading']}\n{entry['content']}")
            ]
            resp = await bridge.chat(messages, temperature=0.6, max_tokens=80)
            caption = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            output_lines.append(f"### {entry['heading']}\n{caption}")
        return "\n\n".join(output_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn a devlog into a product pitch")
    parser.add_argument("devlog", type=Path, help="Path to devlog.md")
    parser.add_argument("--limit", type=int, default=3, help="Number of entries to process")
    parser.add_argument("--out", type=Path, help="Optional file to write the pitch")
    args = parser.parse_args()

    pitch = asyncio.run(generate_pitch(args.devlog, args.limit))
    if args.out:
        args.out.write_text(pitch, encoding="utf-8")
    else:
        print(pitch)


if __name__ == "__main__":
    main()
