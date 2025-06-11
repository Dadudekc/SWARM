"""
Bridge core module containing the main bridge service.
"""

from .bridge import ChatGPTBridge
from .constants import (
    CHATGPT_URL,
    GPT_URL,
    CURRENT_DIR,
    PROFILE_DIR,
    COOKIE_FILE,
    CONTENT_LOG_DIR,
    CHAT_INPUT_SELECTORS,
    SEND_BUTTON_SELECTORS,
    LOGIN_BUTTON_SELECTORS
)

__all__ = [
    'ChatGPTBridge',
    'CHATGPT_URL',
    'GPT_URL',
    'CURRENT_DIR',
    'PROFILE_DIR',
    'COOKIE_FILE',
    'CONTENT_LOG_DIR',
    'CHAT_INPUT_SELECTORS',
    'SEND_BUTTON_SELECTORS',
    'LOGIN_BUTTON_SELECTORS'
] 