"""Site customizations for Dream.OS test environment.

This file is imported automatically by Python at startup (via the `site` module).
We use it here to register placeholder classes and modules required only for
legacy tests that relied on discord.py types or other heavy dependencies.
These placeholders are *only* intended for the test-suite shim layer and
should **never** be referenced by production code.
"""
from __future__ import annotations

import builtins
import types
import sys

# ---------------------------------------------------------------------------
# 1. Stub out basic Discord classes early so that the test utilities that use
#    them in type annotations (which are evaluated eagerly) do not raise
#    NameError at import time.
# ---------------------------------------------------------------------------

_placeholder_names = (
    "Guild",
    "Member",
    "TextChannel",
    "Message",
    "Interaction",
)

for _name in _placeholder_names:
    if _name not in builtins.__dict__:
        builtins.__dict__[_name] = type(_name, (), {})

# ---------------------------------------------------------------------------
# 2. Provide a lightweight shim for the legacy `dreamos.core.ui` package and
#    a handful of its historically public sub-modules. These UI components
#    were removed in the recent refactor but are still referenced by tests.
#    We create empty module objects (with the required public symbols) and
#    register them in `sys.modules` so that `import` statements succeed.
# ---------------------------------------------------------------------------

def _create_stub_module(mod_name: str) -> types.ModuleType:  # noqa: D401
    """Return a fresh stub module registered under *mod_name*."""
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    module = types.ModuleType(mod_name)
    module.__all__ = []  # type: ignore[attr-defined]
    sys.modules[mod_name] = module
    return module

# Root UI package
_ui_root_name = "dreamos.core.ui"
_ui_root = _create_stub_module(_ui_root_name)

# Public API expected by tests
class MainWindow:  # pylint: disable=too-few-public-methods
    """Placeholder for the historical Qt main window."""

    def __init__(self, *args, **kwargs):  # noqa: D401
        pass

_ui_root.MainWindow = MainWindow  # type: ignore[attr-defined]
_ui_root.__all__.append("MainWindow")  # type: ignore[attr-defined]

# Sub-modules commonly imported by the test-suite
_submodules = {
    "log_console": (),
    "log_monitor": (),
    "theme_manager": ("get_dialog_stylesheet", "apply_dialog_theme", "is_dark_theme"),
    "agent_status_panel": (),
    "agent_dashboard": (),
    "agent_monitor": (),
    "main_window": (),
    "test_gui": ("verify_configs", "main"),
}

for sub_name, exports in _submodules.items():
    qualified = f"{_ui_root_name}.{sub_name}"
    mod = _create_stub_module(qualified)
    for fn in exports:
        # Create no-op callables that just return None / False as appropriate.
        def _noop(*_a, **_kw):  # noqa: D401
            return False if fn.startswith("is_") else None

        _noop.__name__ = fn
        setattr(mod, fn, _noop)
        mod.__all__.append(fn)  # type: ignore[attr-defined]

    # Expose the submodule on the root package as attribute
    setattr(_ui_root, sub_name, mod)  # type: ignore[attr-defined]

# The stubs are now live in sys.modules and can be imported by tests.

# ---------------------------------------------------------------------------
# 3. Provide a light-weight shim for the `tqdm` progress-bar library so that
#    test modules importing it don't fail in minimal environments.
# ---------------------------------------------------------------------------
import sys as _sys
import types as _types

if 'tqdm' not in _sys.modules:
    _tqdm = _types.ModuleType('tqdm')

    class _DummyTqdm:  # noqa: D401
        def __init__(self, iterable=None, *args, **kwargs):
            self.iterable = iterable or []
            self.total = len(self.iterable)

        def __iter__(self):
            return iter(self.iterable)

        def update(self, n=1):
            pass

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    _tqdm.tqdm = _DummyTqdm  # type: ignore[attr-defined]
    _tqdm.__all__ = ['tqdm']
    _sys.modules['tqdm'] = _tqdm 