import argparse
from pathlib import Path
from typing import List, Dict

from dreamos.core.ai.dreamscribe import Dreamscribe
from .devlog_pitcher import parse_devlog


def ingest_agent_devlog(agent_id: str, devlog_path: Path, scribe: Dreamscribe) -> List[str]:
    """Ingest all entries from a single devlog file.

    Parameters
    ----------
    agent_id: str
        Identifier for the agent the devlog belongs to.
    devlog_path: Path
        Path to the devlog markdown file.
    scribe: Dreamscribe
        Dreamscribe instance used to store lore.

    Returns
    -------
    List[str]
        IDs of ingested memory fragments.
    """
    entries = parse_devlog(devlog_path)
    memory_ids: List[str] = []
    for entry in entries:
        memory_id = scribe.ingest_devlog({
            "agent_id": agent_id,
            "content": entry.get("content", ""),
            "context": {"heading": entry.get("heading", "")},
        })
        memory_ids.append(memory_id)
    return memory_ids


def ingest_all_devlogs(root: Path, scribe: Dreamscribe) -> Dict[str, List[str]]:
    """Ingest devlogs for all agents found under *root*.

    Parameters
    ----------
    root: Path
        Directory containing ``agent*/devlog.md`` files.
    scribe: Dreamscribe
        Dreamscribe instance used to store lore.

    Returns
    -------
    Dict[str, List[str]]
        Mapping of agent_id to list of ingested memory IDs.
    """
    result: Dict[str, List[str]] = {}
    for devlog in root.glob("agent*/devlog.md"):
        agent_id = devlog.parent.name
        result[agent_id] = ingest_agent_devlog(agent_id, devlog, scribe)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest devlog entries into Dreamscribe lore")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("runtime/devlog/agents"),
        help="Root directory containing agent devlogs",
    )
    args = parser.parse_args()

    scribe = Dreamscribe()
    ingest_all_devlogs(args.root, scribe)


if __name__ == "__main__":
    main()

