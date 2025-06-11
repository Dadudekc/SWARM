"""
Bridge constants and configuration.
"""

import os

# URLs
CHATGPT_URL = "https://chat.openai.com/"
GPT_URL = "https://chatgpt.com/g/g-6817f1a5d2e88191948898629f7e8d9b-protocol-commander-thea"

# Directory paths
CURRENT_DIR = os.path.abspath(os.getcwd())
PROFILE_DIR = os.path.join(CURRENT_DIR, "runtime", "chrome_profile")
COOKIE_FILE = os.path.join(CURRENT_DIR, "runtime", "cookies", "openai.pkl")
CONTENT_LOG_DIR = os.path.join(CURRENT_DIR, "runtime", "chat_logs")

# Ensure directories exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
os.makedirs(CONTENT_LOG_DIR, exist_ok=True)

# Selectors for ChatGPT UI elements
CHAT_INPUT_SELECTORS = [
    'p[data-placeholder="Ask anything"]',  # New primary selector
    'textarea[data-id="chat-input"]',      # Older selector
    'textarea[placeholder="Send a message"]',
    'textarea[aria-label="Chat input"]',
]

SEND_BUTTON_SELECTORS = [
    'button[data-testid="send-button"]',     # Primary test ID
    'button[class*="send"]',                 # Class containing 'send'
    'button[aria-label*="Send"]',            # Aria label containing 'Send'
    "//button[.//span[text()='Send message']]", # XPath for specific text
]

LOGIN_BUTTON_SELECTORS = [
    'button[data-testid="welcome-login-button"]',  # Primary test ID
    'button.btn-primary[data-testid*="login"]',    # Class + test ID
    'button:has(div:contains("Log in"))',         # Contains text
    "//button[.//div[contains(text(), 'Log in')]]", # XPath for text
] 