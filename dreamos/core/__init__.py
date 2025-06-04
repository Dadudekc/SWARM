"""
Core Package

Provides core functionality for the Dream.OS system.
"""

from . import agent_logger
from . import coordinate_manager
from . import cursor_controller
from . import menu
from . import messaging
from . import persistent_queue
from . import system_init

from .cell_phone import CellPhone, send_message
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
