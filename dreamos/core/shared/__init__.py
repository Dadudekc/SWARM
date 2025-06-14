# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from . import coordinate_manager
from . import coordinate_utils
import sys as _sys
import types as _types

__all__ = [
    'coordinate_manager',
    'coordinate_utils',
    'PersistentQueue',
]


# ---------------------------------------------------------------------------
# Lightweight stub for legacy PersistentQueue to break circular imports.
# ---------------------------------------------------------------------------


class PersistentQueue:  # noqa: D401
    """Minimal placeholder – satisfies interface expected by tests."""

    def __init__(self, *args, **kwargs):
        pass

    # Basic queue-like API -------------------------------------------------
    def enqueue(self, item):  # noqa: D401
        return True

    def dequeue(self):  # noqa: D401
        return None

    def peek(self):  # noqa: D401
        return None


# Expose stub as a module to satisfy `import dreamos.core.shared.persistent_queue`
_pq_mod = _types.ModuleType(__name__ + '.persistent_queue')
_pq_mod.PersistentQueue = PersistentQueue  # type: ignore[attr-defined]
_sys.modules[_pq_mod.__name__] = _pq_mod
setattr(_sys.modules[__name__], 'persistent_queue', _pq_mod)
