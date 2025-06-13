"""
Request Queue Module
------------------
Provides request queue management for Dream.OS bridges.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Set

logger = logging.getLogger("request_queue")

@dataclass
class Request:
    """Request in the queue."""
    id: str
    message: str
    timestamp: float
    status: str = "pending"
    response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    last_attempt: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Request':
        """Create request from dictionary."""
        return cls(**data)

class RequestQueue:
    """Manages request queue for bridges."""
    
    def __init__(self, queue_file: str):
        """Initialize request queue.
        
        Args:
            queue_file: Path to queue file
        """
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.requests: Dict[str, Request] = {}
        self._load_requests()
    
    def _load_requests(self):
        """Load requests from file."""
        try:
            if self.queue_file.exists():
                with open(self.queue_file) as f:
                    data = json.load(f)
                    for req in data:
                        self.requests[req["id"]] = Request.from_dict(req)
        except Exception as e:
            logger.error(f"Failed to load requests: {e}")
            self.requests = {}
    
    def _save_requests(self):
        """Save requests to file."""
        try:
            data = [req.to_dict() for req in self.requests.values()]
            with open(self.queue_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save requests: {e}")
    
    def add_request(self, message: str) -> Request:
        """Add request to queue.
        
        Args:
            message: Request message
            
        Returns:
            Created request
        """
        request = Request(
            id=str(uuid.uuid4()),
            message=message,
            timestamp=time.time()
        )
        self.requests[request.id] = request
        self._save_requests()
        return request
    
    def update_request(
        self,
        request_id: str,
        status: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        increment_retry: bool = False
    ):
        """Update request status.
        
        Args:
            request_id: Request ID
            status: New status
            response: Response text
            error: Error message
            increment_retry: Whether to increment retry count
        """
        if request_id in self.requests:
            request = self.requests[request_id]
            request.status = status
            request.response = response
            request.error = error
            request.last_attempt = time.time()
            
            if increment_retry:
                request.retry_count += 1
                
            self._save_requests()
    
    def get_pending_requests(self, max_retries: int = 3) -> List[Request]:
        """Get pending requests.
        
        Args:
            max_retries: Maximum number of retries allowed
            
        Returns:
            List of pending requests
        """
        return [
            req for req in self.requests.values()
            if req.status == "pending" and req.retry_count < max_retries
        ]
    
    def get_requests_by_status(self, status: str, max_age: Optional[int] = None) -> List[Request]:
        """Get requests by status with optional age filtering.
        
        Args:
            status: Request status to filter by
            max_age: Maximum age in seconds
            
        Returns:
            List of matching requests
        """
        now = time.time()
        return [
            req for req in self.requests.values()
            if req.status == status and 
            (max_age is None or now - req.timestamp <= max_age)
        ]
    
    def get_failed_requests(self, max_age: Optional[int] = None) -> List[Request]:
        """Get failed requests.
        
        Args:
            max_age: Maximum age in seconds
            
        Returns:
            List of failed requests
        """
        return self.get_requests_by_status("error", max_age)
    
    def get_completed_requests(self, max_age: Optional[int] = None) -> List[Request]:
        """Get completed requests.
        
        Args:
            max_age: Maximum age in seconds
            
        Returns:
            List of completed requests
        """
        return self.get_requests_by_status("completed", max_age)
    
    def cleanup_old_requests(self, max_age: int = 86400):  # 24 hours
        """Remove requests older than max_age.
        
        Args:
            max_age: Maximum age in seconds
        """
        now = time.time()
        self.requests = {
            id: req for id, req in self.requests.items()
            if now - req.timestamp <= max_age
        }
        self._save_requests()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Dictionary of queue statistics
        """
        now = time.time()
        return {
            "total_requests": len(self.requests),
            "pending_requests": len(self.get_pending_requests()),
            "failed_requests": len(self.get_failed_requests()),
            "completed_requests": len(self.get_completed_requests()),
            "oldest_request": min((req.timestamp for req in self.requests.values()), default=now),
            "newest_request": max((req.timestamp for req in self.requests.values()), default=now)
        } 
