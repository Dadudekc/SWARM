#!/usr/bin/env python3
"""
DevLog Watcher - Monitors local devlogs and syncs them to Discord.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .discord_devlog import DiscordDevlog

logger = logging.getLogger("DevLogWatcher")

class DevLogHandler(FileSystemEventHandler):
    """Handle devlog file changes."""
    
    def __init__(self, agent_id: str, webhook_url: str, footer: str, avatar_url: Optional[str] = None):
        self.agent_id = agent_id
        self.webhook_url = webhook_url
        self.footer = footer
        self.avatar_url = avatar_url
        self.processed_entries: Set[str] = set()
        self.discord_devlog = DiscordDevlog(
            webhook_url=webhook_url,
            agent_name=agent_id,
            footer=footer,
            avatar_url=avatar_url
        )
        
    def _extract_tags(self, content: str) -> Dict[str, str]:
        """Extract tags from devlog content."""
        tags = {}
        tag_pattern = r'#(\w+)(?::([^\s]+))?'
        for match in re.finditer(tag_pattern, content):
            tag, value = match.groups()
            tags[tag] = value or "true"
        return tags
        
    def _parse_entry(self, content: str) -> Optional[Dict]:
        """Parse a devlog entry."""
        # Skip if already processed
        entry_hash = hash(content)
        if entry_hash in self.processed_entries:
            return None
            
        # Extract title and content
        lines = content.strip().split('\n')
        if not lines:
            return None
            
        title = lines[0].strip('# ')
        content = '\n'.join(lines[1:]).strip()
        
        # Extract tags
        tags = self._extract_tags(content)
        
        # Create entry
        entry = {
            'title': title,
            'content': content,
            'tags': tags,
            'timestamp': datetime.now().isoformat()
        }
        
        # Mark as processed
        self.processed_entries.add(entry_hash)
        return entry
        
    async def _process_file(self, file_path: Path):
        """Process a devlog file."""
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                
            entry = self._parse_entry(content)
            if not entry:
                return
                
            # Post to Discord
            success = await self.discord_devlog.update_devlog(
                content=entry['content'],
                title=entry['title'],
                memory_state=entry['tags']
            )
            
            if success:
                logger.info(f"Posted devlog entry for {self.agent_id}")
            else:
                logger.error(f"Failed to post devlog entry for {self.agent_id}")
                
        except Exception as e:
            logger.error(f"Error processing devlog file: {e}")
            
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        if event.src_path.endswith('devlog.md'):
            asyncio.run(self._process_file(Path(event.src_path)))

class DevLogWatcher:
    """Watch and sync devlogs to Discord."""
    
    def __init__(self, config_path: str = "agent_tools/swarm_tools/agent_webhooks.json"):
        self.config_path = Path(config_path)
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, DevLogHandler] = {}
        
    def _load_config(self) -> Dict:
        """Load webhook configuration."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    def start(self):
        """Start watching devlogs."""
        config = self._load_config()
        
        for agent_id, agent_config in config.items():
            # Create handler
            handler = DevLogHandler(
                agent_id=agent_id,
                webhook_url=agent_config['webhook_url'],
                footer=agent_config['footer'],
                avatar_url=agent_config.get('avatar_url')
            )
            
            # Create observer
            observer = Observer()
            log_dir = Path(f"agent_tools/mailbox/{agent_id.lower()}/logs")
            observer.schedule(handler, str(log_dir), recursive=False)
            observer.start()
            
            # Store references
            self.observers[agent_id] = observer
            self.handlers[agent_id] = handler
            
            logger.info(f"Started watching devlogs for {agent_id}")
            
    def stop(self):
        """Stop watching devlogs."""
        for observer in self.observers.values():
            observer.stop()
            observer.join()
            
        logger.info("Stopped watching devlogs")

async def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start watcher
    watcher = DevLogWatcher()
    watcher.start()
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()

if __name__ == "__main__":
    asyncio.run(main()) 
