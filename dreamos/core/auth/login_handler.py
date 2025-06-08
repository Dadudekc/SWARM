"""
Login Handler Shim
----------------
Maintains backward compatibility by re-exporting the handler from its social module location.
"""

from social.strategies.reddit.handlers.login_handler import LoginHandler, LoginError

__all__ = ['LoginHandler', 'LoginError'] 
