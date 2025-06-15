"""Constants for cursor_chatgpt package."""

from pathlib import Path

# Paths and default values
BRIDGE_INBOX = Path("runtime/bridge_inbox/pending_requests.json")
MAX_RETRIES = 3
BASE_WAIT = 3  # seconds
CHATGPT_URL = "https://chat.openai.com/"

__all__ = [
    "BRIDGE_INBOX",
    "MAX_RETRIES",
    "BASE_WAIT",
    "CHATGPT_URL",
]
