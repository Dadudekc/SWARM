"""Stealth browser package for automated web interactions."""
from .stealth_browser import StealthBrowser
from .config import DEFAULT_CONFIG
from .cookie_manager import CookieManager
from .login_handler import LoginHandler

__all__ = ['StealthBrowser', 'DEFAULT_CONFIG', 'CookieManager', 'LoginHandler'] 