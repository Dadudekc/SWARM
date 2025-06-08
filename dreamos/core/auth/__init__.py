"""
Authentication Module
-------------------
Core authentication functionality for Dream.OS.
"""

from .manager import AuthManager, AuthError
from .token import TokenHandler, TokenInfo
from .session import Session, SessionManager
from .login_handler import LoginHandler, LoginError

__all__ = [
    'AuthManager',
    'AuthError',
    'TokenHandler',
    'TokenInfo',
    'Session',
    'SessionManager',
    'LoginHandler',
    'LoginError'
]
