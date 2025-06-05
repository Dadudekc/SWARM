"""
Core Package

Provides core functionality for the Dream.OS system.
"""

try:
    from . import agent_logger
except Exception:  # pragma: no cover - optional dependency
    agent_logger = None
try:
    from . import coordinate_manager
except Exception:  # pragma: no cover - optional dependency
    coordinate_manager = None
try:
    from . import cursor_controller
except Exception:  # pragma: no cover - optional dependency
    cursor_controller = None
try:
    from . import menu
except Exception:  # pragma: no cover - optional dependency
    menu = None
try:
    from . import messaging
except Exception:  # pragma: no cover - optional dependency
    messaging = None
try:
    from . import persistent_queue
except Exception:  # pragma: no cover - optional dependency
    persistent_queue = None
try:
    from . import system_init
except Exception:  # pragma: no cover - optional dependency
    system_init = None

# Import from messaging module
from .messaging.cell_phone import CellPhone, send_message
from .messaging.common import Message, MessageMode, MessagePriority
from .persistent_queue import PersistentQueue

__all__ = [
    'agent_logger',
    'coordinate_manager',
    'cursor_controller',
    'menu',
    'messaging',
    'persistent_queue',
    'system_init',
    'CellPhone',
    'Message',
    'MessageMode',
    'MessagePriority',
    'PersistentQueue',
    'send_message'
]
