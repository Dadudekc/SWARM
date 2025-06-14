# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

"""Agent tools package initialization.

This package previously relied on a ``system_diagnostics`` module that was
removed during refactoring.  Importing ``agent_tools`` on systems where that
module does not exist caused an ``ImportError`` when running tests or scripts.

To provide a smoother experience for developers on machines that do not have
``system_diagnostics`` available, the import is now optional.  If the module is
missing, ``agent_tools`` will still load and expose an empty namespace for it.
This mirrors the behaviour on the original development machine without
breaking other environments.
"""

try:
    from . import system_diagnostics  # type: ignore
except ImportError:  # pragma: no cover - fallback for missing module
    system_diagnostics = None  # type: ignore

__all__ = ["system_diagnostics"]
