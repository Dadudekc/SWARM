# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

from . import agent_interface
from . import agent_loop
from . import cli
from . import config
from . import cursor_controller
from . import log_manager
from . import menu
from . import message
from . import messaging
from . import metrics
from . import system_init
from . import shared
from .config.config_manager import ConfigManager

# Make response_collector_new import optional
try:
    from . import response_collector_new
except ImportError:
    pass  # Optional dependency

__all__ = [
    'agent_interface',
    'agent_loop',
    'cli',
    'config',
    'cursor_controller',
    'log_manager',
    'menu',
    'message',
    'messaging',
    'metrics',
    'response_collector_new',
    'system_init',
    'shared',
]

"""
Dream.OS Core Package

Core functionality for the Dream.OS system.
"""
