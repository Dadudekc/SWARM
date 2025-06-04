"""Deprecated compatibility wrapper for ``dreamos.core.messaging.cell_phone``."""

from warnings import warn

<<<<<<< HEAD
warn(
    "dreamos.core.cell_phone is deprecated; use dreamos.core.messaging.cell_phone instead",
    DeprecationWarning,
    stacklevel=2,
)
=======
import logging
import argparse
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from .persistent_queue import PersistentQueue
from .messaging.common import Message, MessageMode
>>>>>>> origin/codex/refactor-messaging-module-for-shared-enums

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
