"""
Dream.OS Security Namespace

This module provides a unified interface for authentication, session management,
and identity handling in the Dream.OS system.

The security namespace consolidates previously scattered auth/session logic
into a single, well-organized module with clear responsibilities.
"""

from .auth_manager import AuthManager
from .session_manager import SessionManager
from .identity_utils import IdentityUtils
from .security_config import SecurityConfig

__all__ = [
    'AuthManager',
    'SessionManager',
    'IdentityUtils',
    'SecurityConfig'
] 