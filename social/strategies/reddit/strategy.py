"""
Reddit Strategy Module
--------------------
Provides functionality for interacting with Reddit.
"""

from typing import Optional, Dict, Any, List, Tuple
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)
from datetime import datetime, timedelta
import time
import json
import os
from pathlib import Path
import logging

from social.strategies.platform_strategy_base import PlatformStrategy
from social.strategies.reddit.handlers.post_handler import PostHandler
from social.strategies.reddit.handlers.comment_handler import CommentHandler
from social.strategies.reddit.handlers.login_handler import LoginHandler, LoginError
from social.strategies.reddit.validators.media_validator import MediaValidator
from social.strategies.reddit.rate_limiting.rate_limiter import RateLimiter, rate_limit
from dreamos.core.log_manager import LogManager
from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.social.utils.social_common import SocialMediaUtils
from .config import RedditConfig
from dreamos.core.config.config_manager import ConfigManager
from dreamos.core.monitoring.metrics import LogMetrics
from .handlers.login_handler import LoginHandler
from .handlers.post_handler import PostHandler
from .handlers.media_handler import MediaHandler
from ..strategy_base import SocialMediaStrategy

class RedditStrategy(PlatformStrategy):
    """Strategy for interacting with Reddit."""
    
    def __init__(
        self,
        driver,
        config: Dict[str, Any],
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[LogManager] = None
    ):
        """Initialize the Reddit strategy.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
            memory_update: Optional dictionary to store memory updates
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
        """
        # Validate required configuration keys
        if "reddit" not in config:
            raise ValueError("Missing 'reddit' configuration section")
        
        required_keys = ["username", "password", "cookies_path", "profile_path"]
        missing_keys = [key for key in required_keys if key not in config["reddit"]]
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        
        # Ensure window coordinates are available
        if "window_coords" not in config:
            if "browser" in config and "window_size" in config["browser"]:
                config["window_coords"] = {
                    "x": 0,
                    "y": 0,
                    "width": config["browser"]["window_size"]["width"],
                    "height": config["browser"]["window_size"]["height"]
                }
            else:
                raise ValueError("Missing required window coordinates")
        
        if "window_title" not in config:
            if "browser" in config and "window_title" in config["browser"]:
                config["window_title"] = config["browser"]["window_title"]
            else:
                config["window_title"] = "Reddit Browser"
        
        super().__init__(driver, config, memory_update, agent_id, log_manager=log_manager)
        
        # Initialize Reddit-specific config
        self.reddit_config = RedditConfig.from_dict(config.get("reddit", {}))
        
        # Initialize handlers
        self.post_handler = PostHandler(driver, config, memory_update)
        self.comment_handler = CommentHandler(driver, config, memory_update)
        self.login_handler = LoginHandler(
            driver=self.driver,
            config=self.reddit_config,
            memory_update=self.memory_updates,
            logger=self.logger
        )
        
        # Initialize utils
        self.utils = SocialMediaUtils(self.driver, self.reddit_config.__dict__)
        
        # Set media limits
        self.max_images = 20
        self.max_image_size = 20 * 1024 * 1024  # 20MB
        self.max_videos = 1
        self.max_video_size = 100 * 1024 * 1024  # 100MB
        
        # Initialize validators with correct limits
        self.media_validator = MediaValidator(max_files=self.max_images, max_size=self.max_image_size)
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_attempts=3,
            window_seconds=300,
            backoff_factor=2
        )
        
        # Set supported media formats
        self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        self.supported_video_formats = [".mp4", ".mov", ".avi"]
        
        # Initialize session management
        self.session_file = os.path.join(config["reddit"]["cookies_path"], "session.json")
        self.session_timeout = timedelta(hours=24)
        
        # Initialize memory updates
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
                'comment': 0,
                'errors': 0
            }
        }
        
        # Load existing session if available
        self._load_session()
        
        # Store last post data for retry
        self.last_title = None
        self.last_content = None
        self.last_media_files = None

        self._logger = logging.getLogger(self.__class__.__name__)
        
    def record_metric(self, metric_type: str, value: float, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags
            metadata: Optional metadata
        """
        self._metrics.record_metric(metric_type, value, tags, metadata)
        
    def get_metrics(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics with optional filtering.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of metric entries
        """
        return self._metrics.get_metrics(metric_type, start_time, end_time)
        
    def get_summary(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metric summary statistics.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of summary statistics
        """
        return self._metrics.get_summary(metric_type, start_time, end_time)
        
    def save_metrics(self, filepath: Optional[str] = None) -> None:
        """Save metrics to file.
        
        Args:
            filepath: Optional file path to save to
        """
        self._metrics.save_metrics(filepath)
        
    def load_metrics(self, filepath: Optional[str] = None) -> None:
        """Load metrics from file.
        
        Args:
            filepath: Optional file path to load from
        """
        self._metrics.load_metrics(filepath)
        
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self._metrics.clear_metrics()

    def _load_session(self) -> None:
        """Load existing session if available and valid."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    
                # Check if session is still valid
                if self._is_session_valid(session_data):
                    self.driver.add_cookie(session_data['cookies'])
                    self.memory_updates['last_action'] = 'session_loaded'
                    if self.logger:
                        self.logger.info(
                            message="Session loaded successfully",
                            platform="reddit",
                            status="success"
                        )
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message=f"Failed to load session: {str(e)}",
                    platform="reddit",
                    status="error"
                )

    def _save_session(self) -> None:
        """Save current session state."""
        try:
            session_data = {
                'cookies': self.driver.get_cookies(),
                'timestamp': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
                
            if self.logger:
                self.logger.info(
                    message="Session saved successfully",
                    platform="reddit",
                    status="success"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(
                    message=f"Failed to save session: {str(e)}",
                    platform="reddit",
                    status="error"
                )

    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Check if session is still valid."""
        try:
            timestamp = datetime.fromisoformat(session_data['timestamp'])
            return datetime.now() - timestamp < self.session_timeout
        except (KeyError, ValueError):
            return False

    def login(self) -> bool:
        """Login to Reddit.
        
        Returns:
            True if login was successful, False otherwise
        """
        try:
            return self.login_handler.login()
        except Exception as e:
            self._handle_error(str(e), "login")
            return False
    
    def is_logged_in(self) -> bool:
        """Check if currently logged in.
        
        Returns:
            True if logged in, False otherwise
        """
        return self.login_handler.is_logged_in()
    
    def verify_session(self) -> bool:
        """Verify if current session is valid.
        
        Returns:
            True if session is valid, False otherwise
        """
        return self.login_handler.verify_session()

    @rate_limit("post")
    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post on Reddit.
        
        Args:
            title: Post title
            content: Post content
            media_files: Optional list of media file paths
            
        Returns:
            True if post was created successfully, False otherwise
        """
        try:
            # Store post data for potential retry
            self.last_title = title
            self.last_content = content
            self.last_media_files = media_files
            
            # Check if logged in
            if not self.is_logged_in():
                self._handle_error("Not logged in", "post")
                return False
            
            # Validate media files if provided
            is_video = False
            if media_files:
                is_video = any(ext.lower() in self.supported_video_formats for _, ext in map(os.path.splitext, media_files))
                is_valid, error = self.media_validator.validate_media(media_files, is_video)
                if not is_valid:
                    self._handle_error(error, "validate_media")
                    return False
            
            # Create the post
            success = self.post_handler.create_post(content, media_paths=media_files, is_video=is_video)
            
            if success:
                self.memory_updates["last_action"] = "post"
                self.memory_updates["stats"]["posts"] = self.memory_updates["stats"].get("posts", 0) + 1
                return True
            else:
                self._handle_error("Post verification failed", "post")
                return False
                
        except Exception as e:
            self._handle_error(e, "post")
            return False

    def _handle_rate_limit(self, error: str) -> None:
        """Handle rate limit errors.
        
        Args:
            error: Error message
        """
        rate_limit_entry = {
            "error": "Rate limit exceeded",  # Always use consistent error message
            "context": "rate_limit",
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory_updates["last_error"] = rate_limit_entry
        self.memory_updates["last_action"] = "rate_limit"
        
        # Update stats
        self.stats["errors"] += 1
        self.memory_updates["stats"]["errors"] += 1
        
        # Log rate limit error with correct signature
        if self.logger:
            self.logger.error(
                message=f"Rate limit exceeded: {error}",
                platform="reddit",
                status="error"
            )
        
        # Add to retry history
        self._handle_retry("Rate limit exceeded", "rate_limit")
        
        # Always raise exception for rate limit
        raise Exception(f"Rate limit exceeded for post: {error}")

    def _handle_error(self, error: Exception, context: str) -> None:
        """Handle general errors.
        
        Args:
            error: The error that occurred
            context: The context where the error occurred
        """
        self.memory_updates["last_error"] = {
            "error": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.memory_updates["retry_history"].append({
            "error": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
    def post(self, content: str, media_files: Optional[List[str]] = None, title: Optional[str] = None) -> bool:
        """Create a post on Reddit with verification.
        
        Args:
            content: Post content
            media_files: Optional list of media file paths
            title: Optional post title (defaults to "New Post")
            
        Returns:
            True if post was created and verified successfully, False otherwise
        """
        try:
            # Set last action to post first
            self.memory_updates["last_action"] = "post"
            
            # Check if logged in
            if not self.is_logged_in():
                self.memory_updates["last_error"] = {
                    "error": "Not logged in",
                    "context": "post"
                }
                self.memory_updates["stats"]["errors"] += 1
                self.stats["errors"] += 1
                return False  # Keep last_action as "post" for not logged in case
                
            # Use default title if not provided
            post_title = title or "New Post"
                
            # Create post
            success = self.create_post(post_title, content, media_files)
            
            if not success:
                self.memory_updates["last_error"] = {
                    "error": "Post verification failed",
                    "context": "post"
                }
                self.memory_updates["stats"]["errors"] += 1
                self.stats["errors"] += 1
                self.memory_updates["last_action"] = None  # Reset action on verification failure
                return False
                
            # Verify post was created
            if not self.post_handler.verify_post(post_title):
                self.memory_updates["last_error"] = {
                    "error": "Post verification failed",
                    "context": "post"
                }
                self.memory_updates["stats"]["errors"] += 1
                self.stats["errors"] += 1
                self.memory_updates["last_action"] = None  # Reset action on verification failure
                return False
                
            # Update stats
            self.memory_updates["stats"]["posts"] += 1
            self.stats["posts"] += 1
            
            # Clear last error
            self.memory_updates["last_error"] = None
            
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "post"
            }
            self.memory_updates["stats"]["errors"] += 1
            self.stats["errors"] += 1
            self.memory_updates["last_action"] = None  # Reset action on error
            return False

    @rate_limit("comment")
    def comment(self, post_url: str, comment_text: str) -> bool:
        """Add a comment to a post.
        
        Args:
            post_url: URL of the post to comment on
            comment_text: Text of the comment
            
        Returns:
            True if comment was added successfully, False otherwise
        """
        try:
            if not self.is_logged_in():
                self.memory_updates["last_error"] = {
                    "error": "Not logged in",
                    "context": "comment"
                }
                return False
                
            success = self.comment_handler.add_comment(post_url, comment_text)
            if success:
                self.memory_updates["stats"]["comment"] += 1
                self.memory_updates["last_action"] = "comment"
            return success
            
        except WebDriverException as e:
            self.memory_updates["last_error"] = {
                "error": f"Message: {str(e)}\n",
                "context": "comment"
            }
            return False
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "comment"
            }
            return False

    def _validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files.
        
        Args:
            files: List of file paths
            is_video: Whether files are videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check number of files
            if is_video and len(files) > self.reddit_config.max_videos:
                return False, f"Too many video files (max {self.reddit_config.max_videos})"
            elif not is_video and len(files) > self.reddit_config.max_images:
                return False, f"Too many image files (max {self.reddit_config.max_images})"
            
            # Check each file
            for file_path in files:
                path = Path(file_path)
                
                # Check if file exists
                if not path.exists():
                    return False, f"File not found: {file_path}"
                
                # Check file size
                if is_video and path.stat().st_size > self.reddit_config.max_video_size:
                    return False, f"Video file too large: {file_path}"
                
                # Check file format
                ext = path.suffix.lower()
                if is_video and ext not in self.reddit_config.supported_video_formats:
                    return False, f"Unsupported video format: {ext}"
                elif not is_video and ext not in self.reddit_config.supported_image_formats:
                    return False, f"Unsupported image format: {ext}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)

    def retry_operation(self, operation: str, max_retries: Optional[int] = None) -> bool:
        """Retry an operation with exponential backoff.
        
        Args:
            operation: Operation to retry ("post" or "login")
            max_retries: Maximum number of retries (defaults to config value)
            
        Returns:
            True if operation succeeded, False otherwise
        """
        if max_retries is None:
            max_retries = self.reddit_config.max_retries
            
        attempt = 1
        while attempt <= max_retries:
            try:
                # Execute operation
                if operation == "post":
                    if not hasattr(self, 'last_title') or not hasattr(self, 'last_content'):
                        self._handle_error("No previous post to retry", "retry")
                        return False
                    success = self.create_post(
                        self.last_title,
                        self.last_content,
                        getattr(self, 'last_media_files', None)
                    )
                elif operation == "login":
                    success = self.login()
                else:
                    self._handle_error(f"Unknown operation: {operation}", "retry")
                    return False
                    
                if success:
                    return True
                    
                # Only increment retry count if operation failed
                if attempt < max_retries:
                    self._handle_retry(f"Operation {operation} failed", operation)
                    attempt += 1
                    time.sleep(self.calculate_retry_delay(attempt))
                    continue
                else:
                    self._handle_error(f"Operation {operation} failed after {max_retries} retries", "retry")
                    return False
                    
            except Exception as e:
                if attempt < max_retries:
                    self._handle_retry(str(e), operation)
                    attempt += 1
                    time.sleep(self.calculate_retry_delay(attempt))
                    continue
                else:
                    self._handle_error(str(e), operation)
                    return False
                    
        return False 
