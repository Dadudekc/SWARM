"""
Metrics module for backward compatibility during transition.
This module re-exports the new unified metrics classes.
"""

from dreamos.core.metrics import (
    BaseMetrics,
    LogMetrics,
    FileMetrics,
    BridgeMetrics
)

# Re-export all metrics classes
__all__ = [
    'BaseMetrics',
    'LogMetrics',
    'FileMetrics',
    'BridgeMetrics'
] 