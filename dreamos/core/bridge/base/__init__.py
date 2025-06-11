"""
Bridge Base Package
-----------------
Base classes and interfaces for bridge functionality.
"""

from .bridge import BaseBridge, BridgeConfig, BridgeError, ErrorSeverity
from .processor import BridgeProcessor
from .handler import BaseHandler, BridgeHandler

__all__ = [
    'BaseBridge',
    'BridgeConfig',
    'BridgeProcessor',
    'BridgeError',
    'ErrorSeverity',
    'BaseHandler',
    'BridgeHandler'
] 