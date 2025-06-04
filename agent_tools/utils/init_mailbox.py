#!/usr/bin/env python3
"""Initialize and manage agent mailboxes."""

import os
import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger("agent_mailbox")

class AgentMailbox:
    """A class to manage agent mailboxes, including initialization and reset operations."""
    
    def __init__(self, agent_id: str, base_dir: str = "runtime/agent_comms/agent_mailboxes"):
        """
        Initialize the AgentMailbox instance.
        Args:
            agent_id (str): The ID of the agent (e.g., 'Agent-4')
            base_dir (str): Base directory for mailboxes
        Raises:
            ValueError: If agent_id is invalid
            OSError: If base_dir is invalid or cannot be created
        """
        # Validate agent_id
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("Invalid agent_id: must be a non-empty string")
        if any(c in agent_id for c in ['/', '\\', '*', '?', '"', '<', '>', '|', ':']):
            raise ValueError("Invalid agent_id: contains invalid characters")
        self.agent_id = agent_id

        # Validate each component of base_dir for invalid characters
        invalid_dir_chars = set('<>"|?*')
        p = Path(base_dir)
        
        # Check for invalid characters in any path component
        for part in p.parts:
            if any(c in part for c in invalid_dir_chars):
                raise OSError(f"Invalid characters in directory path component: {part}")
        
        # Check if parent directory exists
        parent = p.parent
        if not parent.exists():
            raise OSError(f"Parent directory does not exist: {parent}")
        
        # Check if parent directory is writable
        if not os.access(parent, os.W_OK):
            raise OSError(f"Parent directory is not writable: {parent}")
        
        # If absolute path, check if root/anchor exists
        if p.is_absolute():
            anchor = p.anchor or p.drive
            if anchor and not Path(anchor).exists():
                raise OSError(f"Root/anchor does not exist: {anchor}")
        
        try:
            self.base_dir = p.resolve()
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Directory does not exist or cannot be created: {base_dir}") from e
        
        self.agent_dir = self.base_dir / agent_id.lower()
    
    def _get_initial_state(self, current_time: datetime) -> Dict:
        """
        Get the initial state for an agent's mailbox files.
        Args:
            current_time (datetime): Current timestamp
        Returns:
            dict: Dictionary containing initial states for all files
        """
        return {
            "inbox": {
                "type": "INIT",
                "content": "Welcome to your operational loop. Begin by syncing protocols.",
                "from": "bootstrap",
                "timestamp": current_time.isoformat()
            },
            "status": {
                "agent_id": self.agent_id,
                "last_active": None,
                "current_task": None,
                "status": "idle",
                "cycle_count": 0,
                "error_count": 0,
                "last_inbox_check": None
            },
            "devlog": f"""# {self.agent_id} Devlog\n\n**Initialized:** {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n## 🛠️ Boot Log\n\n- Agent mailbox initialized\n- Status tracking enabled\n- Inbox primed with welcome message\n- Ready for prompt injection\n"""
        }
    
    def _write_mailbox_files(self, initial_state: Dict) -> None:
        """
        Write all mailbox files with the given initial state.
        Args:
            initial_state (dict): Dictionary containing initial states for all files
        """
        # Write inbox.json
        with open(self.agent_dir / "inbox.json", "w", encoding='utf-8') as f:
            json.dump(initial_state["inbox"], f, indent=2)
        # Write status.json
        with open(self.agent_dir / "status.json", "w", encoding='utf-8') as f:
            json.dump(initial_state["status"], f, indent=2)
        # Write devlog.md
        with open(self.agent_dir / "devlog.md", "w", encoding='utf-8') as f:
            f.write(initial_state["devlog"])
    
    def reset(self) -> None:
        """
        Reset the agent mailbox to its initial state.
        Creates a backup of existing mailbox if it exists.
        """
        if self.agent_dir.exists():
            # Create backup
            try:
                backup_dir = self.agent_dir.parent / f"{self.agent_id.lower()}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(self.agent_dir, backup_dir)
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
                
            # Remove existing directory and all contents
            try:
                shutil.rmtree(self.agent_dir)
            except Exception as e:
                logger.error(f"Failed to remove existing mailbox: {e}")
                raise
                
        # Initialize new mailbox
        self.initialize()
    
    def initialize(self) -> None:
        """
        Initialize a new agent mailbox with required files and structure.
        Does nothing if mailbox already exists.
        Raises OSError if directory cannot be created.
        """
        # Check if mailbox already exists
        if self.agent_dir.exists():
            print(f"⚠️  Mailbox for {self.agent_id} already exists. Use --reset to reset it.")
            return
            
        # Try to create directory, raise OSError if fails
        try:
            self.agent_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(f"Directory does not exist or cannot be created: {self.agent_dir}") from e
            
        # Get and write initial state
        current_time = datetime.now()
        initial_state = self._get_initial_state(current_time)
        self._write_mailbox_files(initial_state)
        print(f"✅ Successfully initialized mailbox for {self.agent_id}")
        print(f"📁 Location: {self.agent_dir}")

def main():
    parser = argparse.ArgumentParser(description="Initialize or reset agent mailbox with required files")
    parser.add_argument("--agent", required=True, help="Agent ID (e.g., Agent-4)")
    parser.add_argument("--base-dir", default="runtime/agent_comms/agent_mailboxes",
                      help="Base directory for mailboxes")
    parser.add_argument("--reset", action="store_true",
                      help="Reset existing mailbox to initial state")
    args = parser.parse_args()
    mailbox = AgentMailbox(args.agent, args.base_dir)
    if args.reset:
        mailbox.reset()
    else:
        mailbox.initialize()

if __name__ == "__main__":
    main() 