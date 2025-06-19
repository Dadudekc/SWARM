"""Legacy import shim – re-export everything from *dreamos.discord.webhooks*.

Deprecated: use :pymod:`dreamos.discord.webhooks` directly instead.
"""

from __future__ import annotations

from dreamos.discord.webhooks import *  # noqa: F403,F401 – re-export all symbols

# Some test suites monkeypatch environment variables and call
# ``importlib.reload`` on this module. Under certain conditions (e.g. when the
# module object gets replaced with a lightweight stub) ``__spec__`` may be
# missing, causing *reload* to raise *ImportError*. Ensure a minimal spec is
# always present so reloading behaves predictably.

import importlib.util as _util  # noqa: E402  (local import after star)
import importlib.machinery as _machinery  # noqa: E402

if __spec__ is None:  # pragma: no cover – defensive safety net
    __spec__ = _machinery.ModuleSpec(__name__, loader=_machinery.BuiltinImporter)
