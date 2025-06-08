"""
Social Media Dispatcher
----------------------
Main automation loop that dispatches posts to all platforms.
Handles parallel posting, cookie management, and error recovery.
"""

import os
import time
import threading
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from .driver_manager import DriverManager
from ..config.social_config import social_config, Platform
from dreamos.core.logging.log_manager import LogManager
from dreamos.core.logging.log_config import LogConfig, LogLevel
from .rate_limiter import RateLimiter
from ..strategies.reddit.handlers.login_handler import LoginHandler
from ..utils.media_validator import MediaValidator
from ..strategies import (
    FacebookStrategy,
    TwitterStrategy,
    InstagramStrategy,
    RedditStrategy,
    StockTwitsStrategy,
    LinkedInStrategy
)
from ..strategies.reddit.config import RedditConfig
from dreamos.core.monitoring.metrics import LogMetrics

class SocialPlatformDispatcher:
    """Main dispatcher for handling social media operations."""
    
    def __init__(self, memory_update: Dict[str, Any], headless: Optional[bool] = None):
        """Initialize the dispatcher.
        
        Args:
            memory_update: Dictionary for tracking operation state
            headless: Optional override for headless mode
        """
        self.memory_update = memory_update
        
        # Initialize LogManager with social-specific config
        log_config = LogConfig(
            level=LogLevel.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            file_path=os.path.join("logs/social", "dispatcher.log"),
            max_file_size=10 * 1024 * 1024,  # 10MB
            backup_count=5,
            max_age_days=30
        )
        self.log_manager = LogManager(config=log_config)
        
        # Initialize rate limiter with default limits
        default_limits = {
            "post": {"limit": 50, "window": 3600},  # 50 posts per hour
            "comment": {"limit": 100, "window": 3600},  # 100 comments per hour
            "login": {"limit": 5, "window": 300},  # 5 login attempts per 5 minutes
            "like": {"limit": 200, "window": 3600},  # 200 likes per hour
            "follow": {"limit": 50, "window": 3600},  # 50 follows per hour
            "message": {"limit": 20, "window": 3600},  # 20 messages per hour
        }
        self.rate_limiter = RateLimiter(limits=default_limits)
        
        # Initialize login handler with mock driver and config for testing
        mock_driver = Mock()
        mock_config = RedditConfig(
            username="test_user",
            password="test_pass",
            cookies_path=Path("data/cookies"),
            max_retries=3,
            retry_delay=1,
            session_timeout=24,
            rate_limit_posts=10,
            rate_limit_comments=50,
            supported_image_formats=[".jpg", ".png", ".gif"],
            supported_video_formats=[".mp4", ".mov"],
            max_images=10,
            max_videos=1,
            max_video_size=10 * 1024 * 1024
        )
        self.login_handler = LoginHandler(driver=mock_driver, config=mock_config)
        self.media_validator = MediaValidator()
        self.driver_manager = DriverManager()
        
        # Get platform configurations
        self.platform_configs = {
            platform.name.lower(): social_config.get_platform(platform.name.lower())
            for platform in Platform
        }
        
        # Initialize platform strategies
        self.platforms = {
            "facebook": FacebookStrategy,
            "twitter": TwitterStrategy,
            "instagram": InstagramStrategy,
            "reddit": RedditStrategy,
            "stocktwits": StockTwitsStrategy,
            "linkedin": LinkedInStrategy
        }
        
        # Filter enabled platforms
        self.enabled_platforms = {
            name: strategy
            for name, strategy in self.platforms.items()
            if self.platform_configs[name].config.get("enabled", False)
        }
        
        # Log enabled platforms
        self.log_manager.info(
            message="Social platform dispatcher initialized",
            metadata={
                "enabled_platforms": list(self.enabled_platforms.keys()),
                "headless_mode": headless
            }
        )
        
        # Create session IDs for enabled platforms
        self.session_ids = [f"session_{platform}" for platform in self.enabled_platforms]
        
        # Initialize driver sessions
        self.driver_sessions = self.driver_manager.get_multi_driver_sessions(
            session_ids=self.session_ids,
            proxy_rotation=self.platform_configs["twitter"].config.get("proxy_rotation", False),
            headless=headless if headless is not None else self.platform_configs["twitter"].config.get("headless", False)
        )
        
        # Log driver initialization
        self.log_manager.info(
            message="Driver sessions initialized",
            metadata={
                "session_ids": self.session_ids,
                "proxy_rotation": self.platform_configs["twitter"].config.get("proxy_rotation", False),
                "headless": headless if headless is not None else self.platform_configs["twitter"].config.get("headless", False)
            }
        )
        
    def _update_memory(self, action: str, success: bool, error: Optional[str] = None) -> None:
        """Update memory with action results.
        
        Args:
            action: Action performed
            success: Whether action succeeded
            error: Optional error message
        """
        # Update memory
        self.memory_update["last_action"] = {
            "action": action,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if not success:
            self.memory_update["last_error"] = {
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            
        # Log the update
        if success:
            self.log_manager.info(
                platform="social",
                status=action,
                message=f"Social action completed: {action}",
                metadata={
                    "action": action,
                    "success": success
                }
            )
        else:
            self.log_manager.error(
                platform="social",
                status=action,
                message=f"Social action failed: {action}",
                error=error,
                metadata={
                    "action": action,
                    "success": success
                }
            )
    
    def dispatch_all(self) -> None:
        """Dispatch posts to all enabled platforms in parallel."""
        self.log_manager.write_log(
            platform="dispatcher",
            status="started",
            tags=["dispatch"],
            message="Starting multi-platform dispatch cycle",
            level=LogLevel.INFO
        )
        
        threads = []
        for index, (platform_name, strategy_class) in enumerate(self.enabled_platforms.items()):
            driver_session = self.driver_sessions[index]
            platform_config = self.platform_configs[platform_name]
            
            # Create strategy instance
            strategy = strategy_class(
                driver=driver_session.driver,
                config=platform_config.config,
                memory_update=self.memory_update
            )
            
            # Generate platform-specific content
            content = strategy.create_post()
            
            # Create and start thread
            thread = threading.Thread(
                target=self._process_platform,
                args=(strategy, content, platform_name)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        self.log_manager.write_log(
            platform="dispatcher",
            status="completed",
            tags=["dispatch"],
            message="Dispatch cycle complete. Shutting down drivers",
            level=LogLevel.INFO
        )
        self._shutdown_all_drivers()
    
    def _process_platform(self, strategy: Any, content: str, platform_name: str) -> bool:
        """Process a single platform's posting operation.
        
        Args:
            strategy: Platform strategy instance
            content: Content to post
            platform_name: Name of the platform
            
        Returns:
            bool: True if posting was successful, False otherwise
        """
        max_retries = self.platform_configs[platform_name].config.get("max_retries", 3)
        retry_delay = self.platform_configs[platform_name].config.get("retry_delay", 5)
        
        # Validate media first (single pass)
        if hasattr(strategy, 'media_files'):
            is_valid, error = self.media_validator.validate(
                strategy.media_files,
                is_video=getattr(strategy, 'is_video', False)
            )
            if not is_valid:
                self.log_manager.write_log(
                    platform=platform_name,
                    status="failed",
                    tags=["media_validation"],
                    message="Media validation failed",
                    error=error,
                    level=LogLevel.ERROR
                )
                return False
        
        # Main retry loop
        for attempt in range(max_retries):
            try:
                # Check rate limits
                if not self.rate_limiter.check_rate_limit(platform_name, "post"):
                    self.log_manager.write_log(
                        platform=platform_name,
                        status="rate_limited",
                        tags=["rate_limit"],
                        message="Rate limit exceeded for posting",
                        level=LogLevel.WARNING
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                
                # Handle login
                if not self.login_handler.handle_login(strategy, platform_name, self.log_manager):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                
                # Attempt post
                post_successful = False
                post_error = None
                try:
                    if strategy.post(content):
                        post_successful = True
                    else:
                        post_error = "Post method returned False"
                except Exception as e:
                    post_error = str(e)

                if post_successful:
                    self.log_manager.write_log(
                        platform=platform_name,
                        status="successful",
                        tags=["post"],
                        message="Post operation successful",
                        metadata={"content": content},
                        level=LogLevel.INFO
                    )
                    return True  # Success, exit retry loop
                else:
                    log_message = f"Post failed: {post_error}" if post_error else "Post failed"
                    self.log_manager.write_log(
                        platform=platform_name,
                        status="failed",
                        tags=["post"],
                        message="Post operation failed",
                        error=log_message,
                        level=LogLevel.ERROR
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    
                    # Final attempt failed
                    self.memory_update["last_error"] = {
                        "platform": platform_name,
                        "timestamp": datetime.now().isoformat(),
                        "error": log_message,
                        "context": "post"
                    }
                    return False
                    
            except Exception as e:  # Outer catch-all for issues like login, rate_limit, or unexpected errors
                self.log_manager.write_log(
                    platform=platform_name,
                    status="failed",
                    tags=["error"],
                    message="Operation failed",
                    error=str(e),
                    level=LogLevel.ERROR
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False
        
        return False  # All retries exhausted
    
    def _shutdown_all_drivers(self) -> None:
        """Safely shut down all driver sessions."""
        for session in self.driver_sessions:
            try:
                session.shutdown_driver()
                session.cleanup_profile()
            except Exception as e:
                self.log_manager.write_log(
                    platform="dispatcher",
                    status="error",
                    tags=["shutdown"],
                    error=f"Error shutting down driver session: {str(e)}",
                    level=LogLevel.ERROR
                )

def main():
    """Example usage of the dispatcher."""
    # Example memory update
    example_memory_update = {
        "quest_completions": ["Unified Social Authentication Rituals"],
        "newly_unlocked_protocols": ["Unified Social Logging Protocol"],
        "feedback_loops_triggered": ["Social Media Auto-Dispatcher Loop"]
    }
    
    # Create and run dispatcher
    dispatcher = SocialPlatformDispatcher(example_memory_update)
    dispatcher.dispatch_all()

if __name__ == "__main__":
    main() 
