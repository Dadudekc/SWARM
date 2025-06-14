"""Stubbed ArchitecturalAnalyzer for legacy analyzer tests."""
from __future__ import annotations

from typing import Any, Dict

__all__ = ["ArchitecturalAnalyzer"]


class ArchitecturalAnalyzer:  # noqa: D401
    """Minimal placeholder implementation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.config: Dict[str, Any] = {}

    def analyze_architecture(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:  # noqa: D401
        """Return dummy architectural analysis results."""
        return {"layers": 0} 