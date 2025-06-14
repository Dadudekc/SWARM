"""Stubbed CodeAnalyzer for legacy analyzer tests."""
from __future__ import annotations

from typing import Any, Dict

__all__ = ["CodeAnalyzer"]


class CodeAnalyzer:  # noqa: D401
    """Minimal placeholder implementation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.config: Dict[str, Any] = {}

    def analyze(self, code: str) -> Dict[str, Any]:  # noqa: D401
        """Return a dummy analysis result."""
        return {"lines": len(code.splitlines()), "todo": 0} 