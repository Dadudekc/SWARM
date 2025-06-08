"""
Logout handler for Reddit strategy.
"""

from typing import Optional
from ..config import RedditConfig

class LogoutHandler:
    """Handles logout operations for Reddit strategy."""
    
    def __init__(self, config: RedditConfig):
        """Initialize the logout handler.
        
        Args:
            config: Reddit configuration object
        """
        self.config = config
        
    async def logout(self) -> bool:
        """Perform logout operation.
        
        Returns:
            bool: True if logout was successful, False otherwise
        """
        try:
            # Clear any active sessions
            self.config.clear_session()
            return True
        except Exception as e:
            print(f"Error during logout: {e}")
            return False
            
    async def force_logout(self) -> bool:
        """Force logout by clearing all sessions and tokens.
        
        Returns:
            bool: True if force logout was successful, False otherwise
        """
        try:
            # Clear all sessions and tokens
            self.config.clear_all_sessions()
            return True
        except Exception as e:
            print(f"Error during force logout: {e}")
            return False 
