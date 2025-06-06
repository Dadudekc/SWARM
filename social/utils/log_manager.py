"""Deprecated log manager.\n\nThis module now proxies to :mod:`dreamos.core.log_manager`."""

from dreamos.core.log_manager import LogManager  # type: ignore
from dreamos.core.logging.log_config import LogConfig, LogLevel

__all__ = ["LogManager", "LogConfig", "LogLevel"]
