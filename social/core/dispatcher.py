"""
Social Media Dispatcher
----------------------
Main automation loop that dispatches posts to all platforms.
Handles parallel posting, cookie management, and error recovery.
"""

import os
import time
import threading
from typing import List, Dict, Any
from datetime import datetime

from social.driver_manager import get_multi_driver_sessions
from social.social_config import social_config, get_platform_config, get_global_config
from dreamos.social.log_writer import logger, write_json_log
from social.strategies import (
    FacebookStrategy,
    TwitterStrategy,
    InstagramStrategy,
    RedditStrategy,
    StocktwitsStrategy,
    LinkedInStrategy
)

class SocialPlatformDispatcher:
    """Main dispatcher for handling social media operations."""
    
    def __init__(self, memory_update: Dict[str, Any], headless: bool = None):
        self.memory_update = memory_update
        self.global_config = get_global_config()
        self.headless = headless if headless is not None else self.global_config.get("headless", False)
        
        # Initialize platform strategies
        self.platforms = {
            "facebook": FacebookStrategy,
            "twitter": TwitterStrategy,
            "instagram": InstagramStrategy,
            "reddit": RedditStrategy,
            "stocktwits": StocktwitsStrategy,
            "linkedin": LinkedInStrategy
        }
        
        # Filter enabled platforms
        self.enabled_platforms = {
            name: strategy
            for name, strategy in self.platforms.items()
            if get_platform_config(name).get("enabled", False)
        }
        
        # Create session IDs for enabled platforms
        self.session_ids = [f"session_{platform}" for platform in self.enabled_platforms]
        
        # Initialize driver sessions
        self.driver_sessions = get_multi_driver_sessions(
            session_ids=self.session_ids,
            proxy_rotation=self.global_config.get("proxy_rotation", False),
            headless=self.headless
        )
        
        logger.info(f"Initialized dispatcher with {len(self.enabled_platforms)} enabled platforms")
    
    def dispatch_all(self) -> None:
        """Dispatch posts to all enabled platforms in parallel."""
        logger.info("🚀 Starting multi-platform dispatch cycle...")
        
        threads = []
        for index, (platform_name, strategy_class) in enumerate(self.enabled_platforms.items()):
            driver_session = self.driver_sessions[index]
            platform_config = get_platform_config(platform_name)
            
            # Create strategy instance
            strategy = strategy_class(
                driver=driver_session.driver,
                config=platform_config,
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
        
        logger.info("✅ Dispatch cycle complete. Shutting down drivers...")
        self._shutdown_all_drivers()
    
    def _process_platform(self, strategy: Any, content: str, platform_name: str) -> None:
        """Process a single platform's posting operation."""
        try:
            # Attempt login
            if not strategy.is_logged_in():
                if not strategy.login():
                    logger.error(f"❌ Failed to login to {platform_name}")
                    write_json_log(
                        platform=platform_name,
                        status="failed",
                        tags=["login"],
                        error="Login failed"
                    )
                    return
            
            # Attempt post
            if strategy.post(content):
                logger.info(f"✅ Successfully posted to {platform_name}")
                write_json_log(
                    platform=platform_name,
                    status="successful",
                    tags=["post"],
                    metadata={"content": content}
                )
            else:
                logger.error(f"❌ Failed to post to {platform_name}")
                write_json_log(
                    platform=platform_name,
                    status="failed",
                    tags=["post"],
                    error="Post failed"
                )
                
        except Exception as e:
            logger.error(f"❌ Error processing {platform_name}: {str(e)}")
            write_json_log(
                platform=platform_name,
                status="failed",
                tags=["error"],
                error=str(e)
            )
    
    def _shutdown_all_drivers(self) -> None:
        """Safely shut down all driver sessions."""
        for session in self.driver_sessions:
            try:
                session.shutdown_driver()
                session.cleanup_profile()
            except Exception as e:
                logger.error(f"Error shutting down driver session: {str(e)}")

def main():
    """Example usage of the dispatcher."""
    # Example memory update
    example_memory_update = {
        "quest_completions": ["Unified Social Authentication Rituals"],
        "newly_unlocked_protocols": ["Unified Social Logging Protocol"],
        "feedback_loops_triggered": ["Social Media Auto-Dispatcher Loop"]
    }
    
    # Create and run dispatcher
    dispatcher = SocialPlatformDispatcher(
        memory_update=example_memory_update,
        headless=False  # Set to True for production
    )
    dispatcher.dispatch_all()

if __name__ == "__main__":
    main() 