"""Lightweight logging metrics used by tests.

This module provides a small metrics helper used by the simplified
``LogManager`` tests. It intentionally keeps functionality minimal so it
can operate in environments without optional dependencies.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class LogMetrics:
    """Collects basic metrics about logging activity."""

    def __init__(self, config: Optional[Any] = None) -> None:
        # Determine the directory for saving metrics (if required)
        if config and hasattr(config, "log_dir"):
            self.log_dir = Path(config.log_dir)
        elif isinstance(config, dict):
            self.log_dir = Path(config.get("log_dir", "logs"))
        else:
            self.log_dir = Path("logs")

        self.reset()

    def increment_logs(
        self,
        platform: str,
        level: str,
        status: str,
        format_type: str,
        bytes_written: int = 0,
    ) -> None:
        """Update metrics for a newly written log entry."""
        self.total_logs += 1
        self.total_bytes += bytes_written
        self.platform_counts[platform] = self.platform_counts.get(platform, 0) + 1
        self.level_counts[level] = self.level_counts.get(level, 0) + 1
        self.status_counts[status] = self.status_counts.get(status, 0) + 1
        self.format_counts[format_type] = self.format_counts.get(format_type, 0) + 1
        self._save()

    def record_error(self, message: str) -> None:
        self.error_count += 1
        self.last_error = datetime.now()
        self.last_error_message = message
        self._save()

    def record_rotation(self) -> None:
        self.last_rotation = datetime.now()
        self._save()

    def reset(self) -> None:
        self.total_logs = 0
        self.total_bytes = 0
        self.error_count = 0
        self.last_error: Optional[datetime] = None
        self.last_error_message: Optional[str] = None
        self.last_rotation: Optional[datetime] = None
        self.platform_counts: Dict[str, int] = {}
        self.level_counts: Dict[str, int] = {}
        self.status_counts: Dict[str, int] = {}
        self.format_counts: Dict[str, int] = {}
        self._save()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _save(self) -> None:
        """Persist metrics to ``metrics.json`` for debugging purposes."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            metrics_file = self.log_dir / "metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(self.get_metrics(), f, indent=2, default=str)
        except Exception:
            # Saving metrics should never fail tests
            pass

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_logs": self.total_logs,
            "total_bytes": self.total_bytes,
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
            "last_error_message": self.last_error_message,
            "last_rotation": str(self.last_rotation) if self.last_rotation else None,
            "platform_counts": self.platform_counts,
            "level_counts": self.level_counts,
            "status_counts": self.status_counts,
            "format_counts": self.format_counts,
        }
