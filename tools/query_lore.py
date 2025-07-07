import argparse
from typing import Optional
from pathlib import Path

from dreamos.core.ai.dreamscribe import Dreamscribe


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Dreamscribe lore")
    parser.add_argument("--agent", help="Filter by agent ID")
    parser.add_argument("--start", type=float, help="Filter by start timestamp")
    parser.add_argument("--end", type=float, help="Filter by end timestamp")
    parser.add_argument("--keyword", help="Filter by keyword")
    args = parser.parse_args()

    scribe = Dreamscribe()
    memories = scribe.query_memories(
        agent_id=args.agent,
        start=args.start,
        end=args.end,
        keyword=args.keyword,
    )

    for mem in memories:
        ts = mem.get("timestamp")
        agent = mem.get("agent_id")
        content = mem.get("content", "")
        print(f"{ts} | {agent}: {content}")


if __name__ == "__main__":
    main()

