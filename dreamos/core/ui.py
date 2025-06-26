"""UI entry points for Dream.OS tests.

Provides a lightweight ``MainWindow`` class used by UI tests. If the full
PyQt5-based implementation is unavailable, a minimal stub is provided to
avoid import errors during test collection.
"""

try:
    from .automation.ui.main_window import MainWindow
except Exception:  # pragma: no cover - fallback for missing dependencies
    class MainWindow:  # type: ignore[misc]
        """Fallback stub when PyQt5 is not installed."""

        def show(self) -> None:
            pass

        def close(self) -> None:
            pass

__all__ = ["MainWindow"]
