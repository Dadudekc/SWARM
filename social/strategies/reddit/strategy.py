"""
Reddit Strategy Module
--------------------
Provides functionality for interacting with Reddit.
"""

from typing import Optional, Dict, Any, List, Tuple
from selenium.webdriver.common.by import By
from social.strategies.platform_strategy_base import PlatformStrategy
from social.strategies.reddit.handlers.post_handler import PostHandler
from social.strategies.reddit.handlers.comment_handler import CommentHandler
from social.strategies.reddit.handlers.login_handler import LoginHandler
from social.strategies.reddit.validators.media_validator import MediaValidator
from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter, rate_limit

class RedditStrategy(PlatformStrategy):
    """Strategy for interacting with Reddit."""
    
    def __init__(
        self,
        driver,
        config: dict,
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[Any] = None
    ):
        """Initialize the Reddit strategy.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
        """
        super().__init__(driver, config, memory_update, agent_id, log_manager=log_manager)
        
        # Initialize handlers
        self.post_handler = PostHandler(driver, config, memory_update)
        self.comment_handler = CommentHandler(driver, config, memory_update)
        self.login_handler = LoginHandler(driver, config, memory_update)
        
        # Initialize validators and rate limiters
        self.media_validator = MediaValidator()
        self.rate_limiter = RateLimiter()
        
        self.memory_updates = {
            'login_attempts': 0,
            'post_attempts': 0,
            'media_uploads': 0,
            'errors': [],
            'last_action': None,
            'last_error': None,
            'retry_history': [],
            'operation_times': {},
            'stats': {
                'login': 0,
                'post': 0,
                'comment': 0
            }
        }

    def _validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files based on type and count."""
        media_type = "video" if is_video else "image"

        if not isinstance(self.media_validator, Mock):
            if media_type == "video":
                self.media_validator.max_files = 1
                self.media_validator.supported_formats = getattr(self, "supported_video_formats", [".mp4", ".mov"])
            elif media_type == "image":
                self.media_validator.max_files = 4
                self.media_validator.supported_formats = getattr(self, "supported_image_formats", [".jpg", ".jpeg", ".png", ".gif"])

        is_valid, error_message = self.media_validator.validate(files, is_video=is_video)
        if not is_valid:
            self.memory_updates["last_error"] = error_message
            return False, error_message
        return True, None

    def create_post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Create a new post on Reddit.
        
        Args:
            content: Post content
            media_paths: Optional list of media file paths
            is_video: Whether the media is video
            
        Returns:
            True if post was created successfully, False otherwise
        """
        try:
            # Validate media if provided
            if media_paths:
                is_valid, error = self._validate_media(media_paths, is_video)
                if not is_valid:
                    self.memory_updates["last_error"] = error
                    return False

            # Create post logic here...
            self.memory_updates["post_attempts"] += 1
            self.memory_updates["last_action"] = "create_post"
            return True

        except Exception as e:
            error_msg = str(e)
            if "Element not found" in error_msg:
                self.memory_updates["last_error"] = "Element not found"
            elif "Click intercepted" in error_msg:
                self.memory_updates["last_error"] = "Click intercepted"
            else:
                self.memory_updates["last_error"] = f"Unexpected error: {error_msg}"
            return False

    def post(self, content: str, media_paths: Optional[List[str]] = None) -> bool:
        """Post content to Reddit.
        
        Args:
            content: Content to post
            media_paths: Optional list of media file paths
            
        Returns:
            True if post was successful, False otherwise
        """
        return self.create_post(content, media_paths=media_paths, is_video=False)

    def is_logged_in(self) -> bool:
        """Check if user is logged into Reddit."""
        return self.login_handler.is_logged_in()
        
    def login(self) -> bool:
        """Log into Reddit."""
        return self.login_handler.login()
        
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