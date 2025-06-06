"""Deprecated log writer wrapper.\n\nThis module proxies to :mod:`dreamos.core.logging.log_writer`.\nIt keeps the ``json`` symbol for backward compatibility with older tests."""

import json
from dreamos.core.logging.log_writer import LogWriter
from dreamos.core.logging.log_config import LogConfig, LogLevel

__all__ = ["LogWriter", "LogConfig", "LogLevel", "json"]
