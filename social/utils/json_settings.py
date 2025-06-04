from __future__ import annotations

"""JSON configuration management utilities."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class ConfigNode:
    """Data holder that provides attribute access like a dotmap."""

    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key, value in list(self.data.items()):
            if isinstance(value, dict):
                self.data[key] = ConfigNode(value)

    def __getattr__(self, item: str) -> Any:
        if item in self.data:
            return self.data[item]
        raise AttributeError(item)

    def __iter__(self):
        return iter(self.data)

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def __getitem__(self, item: str) -> Any:
        return self.data[item]

    def as_dict(self) -> Dict[str, Any]:
        def convert(val: Any) -> Any:
            if isinstance(val, ConfigNode):
                return {k: convert(v) for k, v in val.data.items()}
            return val

        return {k: convert(v) for k, v in self.data.items()}


class JSONConfig(ConfigNode):
    """Load configuration from a JSON file."""

    def __init__(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        super().__init__(data)
        self.path = Path(path)

    def reload(self) -> None:
        """Reload configuration from disk."""
        with open(self.path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.__post_init__()
