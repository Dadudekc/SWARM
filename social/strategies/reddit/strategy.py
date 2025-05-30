from typing import Optional, Dict, Any, List
from social.strategies.platform_strategy_base import PlatformStrategy
from social.strategies.reddit.handlers.post_handler import PostHandler
from social.strategies.reddit.handlers.comment_handler import CommentHandler
from social.strategies.reddit.handlers.login_handler import LoginHandler
from social.strategies.reddit.validators.media_validator import MediaValidator
from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter, rate_limit

class RedditStrategy(PlatformStrategy):
    """Main Reddit strategy class that orchestrates all Reddit-specific operations."""
    
    def __init__(
        self,
        driver,
        config: dict,
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[Any] = None
    ):
        super().__init__(driver, config, memory_update, agent_id, log_manager=log_manager)
        
        # Initialize handlers
        self.post_handler = PostHandler(driver, config, memory_update)
        self.comment_handler = CommentHandler(driver, config, memory_update)
        self.login_handler = LoginHandler(driver, config, memory_update)
        
        # Initialize validators and rate limiters
        self.media_validator = MediaValidator()
        self.rate_limiter = RateLimiter()
        
    def is_logged_in(self) -> bool:
        """Check if user is logged into Reddit."""
        return self.login_handler.is_logged_in()
        
    def login(self) -> bool:
        """Log into Reddit."""
        return self.login_handler.login()
        
    def post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Create a new post on Reddit."""
        if not self.is_logged_in():
            self.memory_updates["last_error"] = "Not logged in"
            return False
            
        if media_paths:
            is_valid, error = self.media_validator.validate(media_paths, is_video)
            if not is_valid:
                self.memory_updates["last_error"] = error
                return False
                
        return self.post_handler.create_post(content, media_paths, is_video)
        
    def comment(self, post_url: str, content: str) -> bool:
        """Add a comment to a Reddit post.
        
        Args:
            post_url: URL of the post to comment on
            content: Comment content
            
        Returns:
            bool: True if comment was successful, False otherwise
        """
        if not self.is_logged_in():
            self.memory_updates["last_error"] = "Not logged in"
            return False
            
        return self.comment_handler.create_comment(post_url, content) 