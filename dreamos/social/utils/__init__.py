"""
Social Utils Package
-------------------
Utility modules for social media integration.
"""

from .log_types import RotationConfig
from .log_level import LogLevel
from .log_config import LogConfig
from .log_rotator import LogRotator
from .json_settings import JSONConfig
from .log_manager import LogManager
from dreamos.core.monitoring.metrics import LogMetrics
from .log_writer import LogWriter, LogEntry
from .media_validator import MediaValidator
# ``social_common`` depends on selenium which may not be installed in all
# environments. Import it lazily to avoid import errors during unit tests that
# only require logging utilities.
try:
    from .social_common import SocialMediaUtils
except Exception:  # pragma: no cover - optional dependency
    SocialMediaUtils = None
from .rate_limiter import RateLimiter
from .log_batcher import LogBatcher

__all__ = [
    'RotationConfig',
    'LogLevel',
    'LogConfig',
    'LogRotator',
    'JSONConfig',
    'LogManager',
    'LogMetrics',
    'LogWriter',
    'LogEntry',
    'MediaValidator',
    'SocialMediaUtils',
    'RateLimiter',
    'LogBatcher'
]
