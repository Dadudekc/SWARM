"""Deprecated compatibility wrapper for ``dreamos.core.messaging.cell_phone``."""

from warnings import warn

warn(
    "dreamos.core.cell_phone is deprecated; use dreamos.core.messaging.cell_phone instead",
    DeprecationWarning,
    stacklevel=2,
)

from .messaging.cell_phone import (
    CellPhone,
    send_message,
    parse_args,
    validate_priority,
    cli_main,
)
try:
    from .messaging.captain_phone import CaptainPhone
except Exception:  # pragma: no cover - optional dependency
    CaptainPhone = None

__all__ = [
    "CellPhone",
    "CaptainPhone",
    "send_message",
    "parse_args",
    "validate_priority",
    "cli_main",
]
