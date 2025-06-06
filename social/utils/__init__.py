"""
Social Media Utilities
--------------------
Common utilities for social media operations.
"""

# The social_common module requires selenium which may not be installed in all
# environments (e.g. CI). Import it lazily so other utilities like the
# ``LogManager`` can still be used without pulling in heavy optional
# dependencies.
try:
    from .social_common import SocialMediaUtils
except Exception:  # pragma: no cover - optional dependency
    SocialMediaUtils = None
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.monitoring.metrics import LogMetrics

__all__ = [
    'SocialMediaUtils',
    'LogConfig',
    'LogLevel',
    'LogMetrics'
]
