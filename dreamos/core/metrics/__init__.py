"""
Metrics Package
-------------
Unified metrics collection and reporting.
"""

from .base import BaseMetrics
from .log_metrics import LogMetrics
from .file_metrics import FileMetrics
from .bridge_metrics import BridgeMetrics

__all__ = [
    'BaseMetrics',
    'LogMetrics',
    'FileMetrics',
    'BridgeMetrics'
]

# Create singleton instances
log_metrics = LogMetrics()
file_metrics = FileMetrics()
bridge_metrics = BridgeMetrics() 