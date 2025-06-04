"""
Devlog Manager

Manages developer logs and changelogs for the Dream.OS project.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("social.utils.devlog_manager")

class DevlogManager:
    """Manages developer logs and changelogs."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize devlog manager.
        
        Args:
            log_dir: Optional log directory
        """
        self.log_dir = log_dir or Path("logs/devlogs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def write_devlog(
        self,
        title: str,
        content: str,
        author: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Write a new devlog entry.
        
        Args:
            title: Devlog title
            content: Devlog content
            author: Author name
            tags: Optional list of tags
            metadata: Optional additional metadata
            
        Returns:
            bool: True if successfully written
        """
        try:
            entry = {
                "title": title,
                "content": content,
                "author": author,
                "tags": tags or [],
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title.lower().replace(' ', '_')}.json"
            filepath = self.log_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(entry, f, indent=2)
            
            logger.info(f"Wrote devlog entry: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing devlog entry: {e}")
            return False
    
    def read_devlog(self, filename: str) -> Optional[Dict]:
        """Read a devlog entry.
        
        Args:
            filename: Name of the devlog file
            
        Returns:
            Optional[Dict]: Devlog entry if found
        """
        try:
            filepath = self.log_dir / filename
            if not filepath.exists():
                return None
                
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading devlog entry: {e}")
            return None
    
    def list_devlogs(
        self,
        author: Optional[str] = None,
        tag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """List devlog entries with optional filtering.
        
        Args:
            author: Optional author to filter by
            tag: Optional tag to filter by
            start_date: Optional start date to filter by
            end_date: Optional end date to filter by
            
        Returns:
            List[Dict]: List of matching devlog entries
        """
        try:
            entries = []
            for filepath in self.log_dir.glob("*.json"):
                with open(filepath, 'r') as f:
                    entry = json.load(f)
                    
                # Apply filters
                if author and entry["author"] != author:
                    continue
                    
                if tag and tag not in entry["tags"]:
                    continue
                    
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if start_date and timestamp < start_date:
                    continue
                    
                if end_date and timestamp > end_date:
                    continue
                    
                entries.append(entry)
            
            return sorted(entries, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing devlog entries: {e}")
            return []
    
    def update_devlog(
        self,
        filename: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update an existing devlog entry.
        
        Args:
            filename: Name of the devlog file
            title: Optional new title
            content: Optional new content
            tags: Optional new tags
            metadata: Optional new metadata
            
        Returns:
            bool: True if successfully updated
        """
        try:
            entry = self.read_devlog(filename)
            if not entry:
                return False
                
            if title:
                entry["title"] = title
            if content:
                entry["content"] = content
            if tags:
                entry["tags"] = tags
            if metadata:
                entry["metadata"].update(metadata)
                
            entry["last_modified"] = datetime.now().isoformat()
            
            filepath = self.log_dir / filename
            with open(filepath, 'w') as f:
                json.dump(entry, f, indent=2)
            
            logger.info(f"Updated devlog entry: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating devlog entry: {e}")
            return False
    
    def delete_devlog(self, filename: str) -> bool:
        """Delete a devlog entry.
        
        Args:
            filename: Name of the devlog file
            
        Returns:
            bool: True if successfully deleted
        """
        try:
            filepath = self.log_dir / filename
            if not filepath.exists():
                return False
                
            filepath.unlink()
            logger.info(f"Deleted devlog entry: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting devlog entry: {e}")
            return False 