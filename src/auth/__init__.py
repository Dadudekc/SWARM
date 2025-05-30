"""
Authentication system package.
"""

from .interface import AbstractAuthInterface, AuthError
from .manager import AuthManager
from .retry import RetryMechanism, RetryError, retry
from .session import SessionManager, Session
from .token import TokenHandler, TokenInfo

__all__ = [
    'AbstractAuthInterface',
    'AuthError',
    'AuthManager',
    'RetryMechanism',
    'RetryError',
    'retry',
    'SessionManager',
    'Session',
    'TokenHandler',
    'TokenInfo'
]

__version__ = '1.0.0' 