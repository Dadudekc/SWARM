"""Simple task handler for captain prompt."""
from pathlib import Path
import json
from typing import Optional

class TaskHandler:
    def __init__(self, base_dir: str = "messages"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.base_dir / "tasks.json"
        if not self.tasks_file.exists():
            self.tasks_file.write_text("{}")

    def get_agent_task(self, agent_id: str) -> Optional[str]:
        """Return the current task string for an agent if available."""
        try:
            data = json.loads(self.tasks_file.read_text())
            return data.get(agent_id)
        except Exception:
            return None

