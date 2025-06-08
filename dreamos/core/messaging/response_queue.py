"""
Response Queue
------------
Thread-safe response queue with persistence and state tracking.
Extends MessageQueue with response-specific functionality.
"""

import json
import logging
import threading
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from uuid import uuid4

from .message_queue import MessageQueue

logger = logging.getLogger(__name__)

class ResponseState(Enum):
    """Response state enumeration."""
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"

class ResponseQueue(MessageQueue):
    """Thread-safe response queue with persistence and state tracking."""
    
    def __init__(self, runtime_dir: Path):
        """Initialize response queue.
        
        Args:
            runtime_dir: Base runtime directory for response storage
        """
        super().__init__()
        self.runtime_dir = runtime_dir
        self.outbox_dir = runtime_dir / "response_outbox"
        self.archive_dir = runtime_dir / "response_archive"
        
        # Create directories
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing responses
        self._load_responses()
        
    def _get_agent_dir(self, agent_id: str) -> Path:
        """Get agent's response directory.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Path to agent's response directory
        """
        return self.outbox_dir / agent_id
        
    def _get_response_path(self, agent_id: str, response_id: str) -> Path:
        """Get path for response file.
        
        Args:
            agent_id: Agent identifier
            response_id: Response identifier
            
        Returns:
            Path to response file
        """
        return self._get_agent_dir(agent_id) / f"{response_id}.json"
        
    def _load_responses(self) -> None:
        """Load existing responses from disk."""
        try:
            for agent_dir in self.outbox_dir.iterdir():
                if not agent_dir.is_dir():
                    continue
                    
                agent_id = agent_dir.name
                for response_file in agent_dir.glob("*.json"):
                    try:
                        with open(response_file, 'r') as f:
                            response = json.load(f)
                            # Add to in-memory queue
                            self.enqueue(agent_id, response)
                    except Exception as e:
                        logger.error(f"Failed to load response {response_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load responses: {e}")
            
    def enqueue_response(self, agent_id: str, payload: Dict[str, Any]) -> Optional[str]:
        """Add response to queue and persist to disk.
        
        Args:
            agent_id: Agent identifier
            payload: Response payload
            
        Returns:
            Response ID if successful, None otherwise
        """
        try:
            # Generate response ID
            response_id = str(uuid4())
            
            # Create response object
            response = {
                "id": response_id,
                "agent_id": agent_id,
                "payload": payload,
                "state": ResponseState.PENDING.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create agent directory
            agent_dir = self._get_agent_dir(agent_id)
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to disk
            response_path = self._get_response_path(agent_id, response_id)
            with open(response_path, 'w') as f:
                json.dump(response, f, indent=2)
                
            # Add to queue
            if self.enqueue(agent_id, response):
                return response_id
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to enqueue response: {e}")
            return None
            
    def update_response_state(self, agent_id: str, response_id: str, state: ResponseState) -> bool:
        """Update response state.
        
        Args:
            agent_id: Agent identifier
            response_id: Response identifier
            state: New state
            
        Returns:
            True if successful
        """
        try:
            response_path = self._get_response_path(agent_id, response_id)
            if not response_path.exists():
                return False
                
            # Read current response
            with open(response_path, 'r') as f:
                response = json.load(f)
                
            # Update state
            response["state"] = state.value
            response["updated_at"] = datetime.utcnow().isoformat()
            
            # Write back
            with open(response_path, 'w') as f:
                json.dump(response, f, indent=2)
                
            # Update in-memory queue
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                for i, msg in enumerate(queue):
                    if msg["id"] == response_id:
                        queue[i] = response
                        break
                        
            return True
            
        except Exception as e:
            logger.error(f"Failed to update response state: {e}")
            return False
            
    def archive_response(self, agent_id: str, response_id: str) -> bool:
        """Archive response.
        
        Args:
            agent_id: Agent identifier
            response_id: Response identifier
            
        Returns:
            True if successful
        """
        try:
            response_path = self._get_response_path(agent_id, response_id)
            if not response_path.exists():
                return False
                
            # Create archive directory
            archive_dir = self.archive_dir / agent_id
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Move to archive
            archive_path = archive_dir / response_path.name
            response_path.rename(archive_path)
            
            # Remove from queue
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                queue[:] = [msg for msg in queue if msg["id"] != response_id]
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive response: {e}")
            return False
            
    def get_pending_responses(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all pending responses for agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of pending responses
        """
        try:
            with self._get_lock(agent_id):
                queue = self._get_queue(agent_id)
                return [
                    msg for msg in queue 
                    if msg["state"] == ResponseState.PENDING.value
                ]
                
        except Exception as e:
            logger.error(f"Failed to get pending responses: {e}")
            return []
            
    def cleanup_old_responses(self, max_age_days: int = 7) -> None:
        """Clean up old responses.
        
        Args:
            max_age_days: Maximum age in days
        """
        try:
            cutoff = datetime.utcnow().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for agent_dir in self.outbox_dir.iterdir():
                if not agent_dir.is_dir():
                    continue
                    
                agent_id = agent_dir.name
                for response_file in agent_dir.glob("*.json"):
                    try:
                        # Check file age
                        if response_file.stat().st_mtime < cutoff:
                            # Archive old response
                            response_id = response_file.stem
                            self.archive_response(agent_id, response_id)
                    except Exception as e:
                        logger.error(f"Failed to cleanup response {response_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup responses: {e}") 