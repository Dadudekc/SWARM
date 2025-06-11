"""
Bridges agent devlogs with social media posting.
Watches devlog files and dispatches updates to configured platforms.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.file_ops import ensure_dir, read_json, write_json
from dreamos.social.platform_poster import PlatformPoster
from dreamos.social.utils.social_common import SocialConfig

logger = get_logger(__name__)

class DevlogEvent(FileSystemEventHandler):
    """Handles devlog file system events."""
    
    def __init__(self, dispatcher: 'DevlogDispatcher'):
        self.dispatcher = dispatcher
        
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.md', '.json')):
            self.dispatcher.process_devlog(event.src_path)

class DevlogDispatcher:
    """Dispatches devlog updates to social media platforms."""
    
    def __init__(self, config: Optional[SocialConfig] = None):
        self.config = config or SocialConfig()
        self.poster = PlatformPoster(config)
        self.post_log_path = Path("dreamos/social/logs/social_post_log.json")
        self.posted_hashes: Set[str] = set()
        self.platforms = self._load_platforms()
        self._load_post_log()
        
    def _load_platforms(self) -> List[str]:
        """Load configured platforms from config."""
        platforms = self.config.get("social", "platforms", default=["discord", "twitter", "reddit"])
        if isinstance(platforms, str):
            platforms = platforms.split(",")
        return [p.strip().lower() for p in platforms]
        
    def _load_post_log(self):
        """Load post history to prevent duplicates."""
        if self.post_log_path.exists():
            try:
                log_data = read_json(self.post_log_path)
                self.posted_hashes = set(log_data.get("hashes", []))
            except Exception as e:
                logger.error("Failed to load post log: %s", e)
                self.posted_hashes = set()
                
    def _save_post_log(self):
        """Save post history."""
        ensure_dir(self.post_log_path.parent)
        write_json(self.post_log_path, {
            "hashes": list(self.posted_hashes),
            "last_updated": time.time()
        })
        
    def _compute_hash(self, content: str) -> str:
        """Compute hash of content to prevent duplicates."""
        return hashlib.sha256(content.encode()).hexdigest()
        
    def _format_devlog_content(self, content: Dict) -> str:
        """Format devlog content for social media."""
        # Basic formatting - can be enhanced with social_formatter.py later
        agent = content.get("agent", "Unknown Agent")
        task = content.get("task", "Unknown Task")
        status = content.get("status", "completed")
        emoji = content.get("emoji", "✅")
        
        return f"{agent} {status} {task} {emoji}"
        
    def process_devlog(self, file_path: str):
        """Process a devlog file for posting."""
        try:
            # Read devlog content
            if file_path.endswith('.json'):
                content = read_json(file_path)
            else:  # .md file
                with open(file_path, 'r') as f:
                    content = {"content": f.read()}
                    
            # Skip if already posted
            content_hash = self._compute_hash(str(content))
            if content_hash in self.posted_hashes:
                logger.debug("Skipping already posted content: %s", content_hash)
                return
                
            # Format and post to each platform
            formatted_content = self._format_devlog_content(content)
            for platform in self.platforms:
                try:
                    success = self.poster.post(platform, formatted_content)
                    if success:
                        logger.info("Posted to %s: %s", platform, formatted_content)
                    else:
                        logger.error("Failed to post to %s", platform)
                except Exception as e:
                    logger.error("Error posting to %s: %s", platform, e)
                    
            # Update post log
            self.posted_hashes.add(content_hash)
            self._save_post_log()
            
        except Exception as e:
            logger.exception("Error processing devlog: %s", e)
            
    def start_watching(self, watch_path: str):
        """Start watching devlog directory for changes."""
        try:
            event_handler = DevlogEvent(self)
            observer = Observer()
            observer.schedule(event_handler, watch_path, recursive=True)
            observer.start()
            logger.info("Started watching devlog directory: %s", watch_path)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                logger.info("Stopped watching devlog directory")
                
            observer.join()
            
        except Exception as e:
            logger.exception("Error watching devlog directory: %s", e)
            
    def cleanup(self):
        """Clean up resources."""
        self.poster.cleanup() 