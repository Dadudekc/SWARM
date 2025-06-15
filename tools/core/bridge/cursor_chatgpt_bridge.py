"""Deprecated shim for backward compatibility."""

import warnings

from .cursor_chatgpt.driver import DriverManager
from .cursor_chatgpt.scraper import ChatScraperService
from .cursor_chatgpt.prompt_exec import PromptExecutionService
from .cursor_chatgpt.memory import AletheiaPromptManager, FeedbackEngine
from .cursor_chatgpt.controller import ChatCycleController
from .cursor_chatgpt.utils import sanitize_filename
from .cursor_chatgpt.constants import (
    BRIDGE_INBOX,
    MAX_RETRIES,
    BASE_WAIT,
    CHATGPT_URL,
)

warnings.warn(
    "cursor_chatgpt_bridge module is deprecated; use tools.core.bridge.cursor_chatgpt instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "DriverManager",
    "ChatScraperService",
    "PromptExecutionService",
    "AletheiaPromptManager",
    "FeedbackEngine",
    "ChatCycleController",
    "sanitize_filename",
    "BRIDGE_INBOX",
    "MAX_RETRIES",
    "BASE_WAIT",
    "CHATGPT_URL",
]

