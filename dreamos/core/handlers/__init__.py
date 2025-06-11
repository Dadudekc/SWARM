"""
Handler Package
-------------
Core handler functionality for the system.
"""

from .unified_handler import UnifiedHandler
from .handler_utils import (
    safe_watch_file,
    structured_log,
    standard_result_wrapper,
    safe_json_operation
)

__all__ = [
    'UnifiedHandler',
    'safe_watch_file',
    'structured_log',
    'standard_result_wrapper',
    'safe_json_operation'
] 