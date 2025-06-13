"""Development log manager for agent control."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class DevLogManager:
    """Manages development logs for agent control."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize the devlog manager.
        
        Args:
            log_dir: Directory to store logs. Defaults to 'logs/devlog'.
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs/devlog")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logs = {}
        self.log_manager = logging.getLogger("devlog")
        
    def log_event(self, agent_id: str, event: str, data: Dict[str, Any]) -> None:
        """Log an event to the devlog.
        
        Args:
            agent_id: ID of the agent
            event: Type of event (e.g. 'started', 'completed')
            data: Event data to log
        """
        agent_dir = self.log_dir / agent_id
        agent_dir.mkdir(exist_ok=True)
        
        log_file = agent_dir / "devlog.md"
        timestamp = datetime.now().isoformat()
        
        # Create or append to log file
        with open(log_file, "a") as f:
            f.write(f"\n## {event} at {timestamp}\n\n")
            for key, value in data.items():
                f.write(f"- {key}: {value}\n")
                
        logger.debug(f"Logged {event} event for {agent_id}")
        
    def get_log(self, agent_id: str) -> Optional[str]:
        """Get log contents for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Log contents or None if not found
        """
        log_file = self.log_dir / agent_id / "devlog.md"
        if not log_file.exists():
            return None
            
        return log_file.read_text()
        
    def clear_log(self, agent_id: str) -> bool:
        """Clear log for an agent with backup.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        log_file = self.log_dir / agent_id / "devlog.md"
        if not log_file.exists():
            return False
            
        # Create backup
        backup_file = log_file.with_suffix(".backup")
        shutil.copy2(log_file, backup_file)
        
        # Clear log
        timestamp = datetime.now().isoformat()
        with open(log_file, "w") as f:
            f.write(f"# {agent_id} Devlog\n\n")
            f.write(f"Log cleared at {timestamp}\n")
            
        return True
        
    def send_embed(self, agent_id: str, title: str, description: str, 
                  color: int = 0x000000, fields: Optional[Dict[str, str]] = None) -> bool:
        """Send an embed message to the log.
        
        Args:
            agent_id: ID of the agent
            title: Embed title
            description: Embed description
            color: Embed color in hex
            fields: Optional fields to include
            
        Returns:
            True if successful, False otherwise
        """
        agent_dir = self.log_dir / agent_id
        agent_dir.mkdir(exist_ok=True)
        
        log_file = agent_dir / "devlog.md"
        timestamp = datetime.now().isoformat()
        
        with open(log_file, "a") as f:
            f.write(f"\n## {title} at {timestamp}\n\n")
            f.write(f"{description}\n\n")
            
            if fields:
                for key, value in fields.items():
                    f.write(f"**{key}**: {value}\n")
                    
        return True
        
    def shutdown(self) -> None:
        """Cleanup resources."""
        # Nothing to clean up
        pass 
