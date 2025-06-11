"""
Metrics utilities for Dream.OS.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class Counter:
    def __init__(self, name: str, description: str, labels: List[str], path: str = "runtime/metrics/counters.json"):
        self.name = name
        self.description = description
        self.labels = labels
        self.path = Path(path)
        self._counters: Dict[str, int] = {}
        self._current_labels: Dict[str, str] = {}
        
        # Ensure metrics directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load()
        
    def _load(self) -> None:
        if not self.path.exists():
            return
            
        try:
            with self.path.open("r") as f:
                self._counters = json.load(f)
        except json.JSONDecodeError:
            self._counters = {}
            
    def _save(self) -> None:
        try:
            with self.path.open("w") as f:
                json.dump(self._counters, f, indent=2)
        except Exception:
            pass
            
    def labels(self, **kwargs: str) -> 'Counter':
        self._current_labels = kwargs
        return self
        
    def inc(self, value: int = 1) -> None:
        key = f"{self.name}:{str(self._current_labels)}"
        self._counters[key] = self._counters.get(key, 0) + value
        self._save()
        
    def log_event(self, event: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        self.inc()
        self._counters[f"{event}_last_time"] = timestamp
        self._save()

__all__ = ["Counter"] 