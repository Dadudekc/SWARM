"""Compatibility wrapper for the messaging ``CellPhone`` implementation."""

from .messaging.cell_phone import (
    CellPhone,
    send_message,
    parse_args,
    validate_priority,
    cli_main,
)
from .messaging.captain_phone import CaptainPhone

__all__ = [
    "CellPhone",
    "CaptainPhone",
    "send_message",
    "parse_args",
    "validate_priority",
    "cli_main",
]
