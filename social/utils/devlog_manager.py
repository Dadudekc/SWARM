"""
Development Log Manager
--------------------
Manages development logs for agents and system components.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import shutil

from .log_manager import LogManager
from .log_config import LogConfig

logger = logging.getLogger('devlog')

class DevlogManager:
    """Manages development logs for agents and system components."""
    
    def __init__(self, log_dir: str = "logs/devlog"):
        """Initialize DevlogManager.
        
        Args:
            log_dir: Directory to store devlogs
        """
        self.log_dir = Path(log_dir)
        self.logs: Dict[str, Any] = {}
        self._shutdown = False
        
        # Initialize LogManager with devlog-specific config
        log_config = LogConfig(
            log_dir=str(self.log_dir),
            batch_size=1,  # No batching for devlogs to ensure immediate writes
            batch_timeout=0.1,  # Minimal timeout
            max_retries=2,
            retry_delay=0.1
        )
        self.log_manager = LogManager(config=log_config)
        
    def _ensure_agent_dir(self, agent_id: str) -> Path:
        """Ensure agent directory exists.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Path: Path to agent directory
        """
        agent_dir = self.log_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir
        
    def _ensure_log_header(self, log_path: Path, agent_id: str) -> None:
        """Ensure log file has proper header.
        
        Args:
            log_path: Path to log file
            agent_id: ID of the agent
        """
        if not log_path.exists():
            with open(log_path, "w") as f:
                f.write(f"# {agent_id} Devlog\n\n")
                f.write("## Events\n\n")
        
    def log_event(self, agent_id: str, event: str, data: Optional[Dict] = None) -> bool:
        """Log an event for an agent.
        
        Args:
            agent_id: ID of the agent
            event: Event type
            data: Optional event data
            
        Returns:
            bool: True if successful
            
        Raises:
            RuntimeError: If manager is shut down
            ValueError: If agent_id or event is empty
        """
        if self._shutdown:
            raise RuntimeError("DevlogManager has been shut down")
            
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string")
            
        if not event or not isinstance(event, str):
            raise ValueError("event must be a non-empty string")
            
        logger.debug(f"Logging event for {agent_id}: {event}")
        
        try:
            # Ensure agent directory exists
            self._ensure_agent_dir(agent_id)
            
            # Store in memory
            if agent_id not in self.logs:
                self.logs[agent_id] = []
            self.logs[agent_id].append({"event": event, "data": data})
            
            # Write to devlog.md
            log_path = self.log_dir / f"{agent_id}/devlog.md"
            self._ensure_log_header(log_path, agent_id)
            
            with open(log_path, "a") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"\n### {event} ({timestamp})\n")
                if data:
                    f.write("```json\n")
                    f.write(json.dumps(data, indent=2))
                    f.write("\n```\n")
                f.write("\n")
            
            # Also log to LogManager for metrics
            self.log_manager.write_log(
                platform="devlog",
                status=event,
                message=f"Devlog event for {agent_id}",
                metadata={
                    "agent_id": agent_id,
                    "event": event,
                    "data": data
                },
                format="text"
            )
            
            # Force flush
            self.log_manager.flush()
            
            return True
        except Exception as e:
            logger.error(f"Error logging event for {agent_id}: {str(e)}")
            return False
        
    def get_log(self, agent_id: str) -> Optional[str]:
        """Get log contents for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Optional[str]: Log contents or None if not found
        """
        if self._shutdown:
            raise RuntimeError("DevlogManager has been shut down")
            
        log_path = self.log_dir / f"{agent_id}/devlog.md"
        if not log_path.exists():
            return None
            
        try:
            return log_path.read_text()
        except Exception as e:
            logger.error(f"Error reading log for {agent_id}: {str(e)}")
            return None
            
    def clear_log(self, agent_id: str) -> bool:
        """Clear log for an agent with backup.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if successful
        """
        if self._shutdown:
            raise RuntimeError("DevlogManager has been shut down")
            
        log_path = self.log_dir / f"{agent_id}/devlog.md"
        if not log_path.exists():
            return False
            
        try:
            # Create backup
            backup_path = log_path.with_suffix(".backup")
            shutil.copy2(log_path, backup_path)
            
            # Write new log with header
            with open(log_path, "w") as f:
                f.write(f"# {agent_id} Devlog\n\n")
                f.write(f"Log cleared at {datetime.now().isoformat()}\n")
                
            return True
        except Exception as e:
            logger.error(f"Error clearing log for {agent_id}: {str(e)}")
            return False
            
    def send_embed(self, agent_id: str, title: str, description: str, color: int = 0x000000, fields: Optional[Dict[str, str]] = None) -> bool:
        """Send an embedded message to the devlog.
        
        Args:
            agent_id: ID of the agent
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: Optional fields dictionary
            
        Returns:
            bool: True if successful
        """
        if self._shutdown:
            raise RuntimeError("DevlogManager has been shut down")
            
        try:
            # Construct embed data
            embed_data = {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Log as embed event
            return self.log_event(
                agent_id=agent_id,
                event="embed",
                data=embed_data
            )
        except Exception as e:
            logger.error(f"Error sending embed for {agent_id}: {str(e)}")
            return False
            
    def shutdown(self) -> None:
        """Shutdown the devlog manager."""
        if not self._shutdown:
            self._shutdown = True
            self.log_manager.shutdown() 