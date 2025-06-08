"""Exceptions for Reddit strategy."""

class RedditError(Exception):
    """Base class for Reddit strategy exceptions."""
    pass

class LogoutError(RedditError):
    """Raised when logout fails due to session/auth issues."""
    pass

class LoginError(RedditError):
    """Exception raised when login fails."""
    pass

class PostError(RedditError):
    """Raised when post operations fail."""
    pass

class MediaError(RedditError):
    """Exception raised when media operations fail."""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class RateLimitError(RedditError):
    """Raised when rate limit is exceeded."""
    pass

__all__ = ['LogoutError', 'AuthenticationError', 'RateLimitError', 'PostError'] 
