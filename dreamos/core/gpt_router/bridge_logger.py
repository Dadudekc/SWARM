"""
Bridge Logger
-------------
Logs prompt and response pairs with metadata.
"""

import json
from pathlib import Path
from typing import Any, Dict


class BridgeLogger:
    """Simple JSON line logger."""

    def __init__(self, log_path: Path | str = "runtime/bridge_log.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: Dict[str, Any]):
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
