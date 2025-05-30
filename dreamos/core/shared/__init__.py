"""
Shared Package

Provides shared utilities and managers for the Dream.OS system.
"""

from .config_manager import ConfigManager
from .coordinate_manager import CoordinateManager

__all__ = [
    'ConfigManager',
    'CoordinateManager',
]
