"""Stubbed ASTAnalyzer for legacy analyzer tests."""
from __future__ import annotations

from typing import Any, Dict

__all__ = ["ASTAnalyzer"]


class ASTAnalyzer:  # noqa: D401
    """Minimal placeholder implementation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.config: Dict[str, Any] = {}

    def analyze_source(self, source_code: str) -> Dict[str, Any]:  # noqa: D401
        """Return dummy AST analysis results."""
        return {"nodes": len(source_code.splitlines()), "functions": 0, "classes": 0} 