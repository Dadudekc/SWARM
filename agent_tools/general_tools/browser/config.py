"""Configuration settings for the stealth browser."""
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    'target_url': 'https://chat.openai.com/codex',
    'page_load_wait': 30,
    'element_wait': 15,
    'headless': False,
    'window_size': (1920, 1080),
    'cookies_file': 'codex_cookies.json',
    'credentials': {
        'email': 'dadudekc@gmail.com',  # Replace with your email
        'password': 'Falcons#1247'    # Replace with your password
    },
    'codex_selectors': {
        'initial_login_button': 'button:contains("Log in to try it")',
        'secondary_login_button': 'button:contains("Log in")',
        'email_input': '#\\:r1\\:-email',
        'password_input': 'input[type="password"]',
        'continue_button': 'button._root_625o4_51._primary_625o4_86[type="submit"][name="intent"][value="email"]',
        'response_area': 'div[role="textbox"]'
    }
} 