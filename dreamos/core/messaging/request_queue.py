"""
Request Queue Module
------------------
Provides request queue management for Dream.OS bridges.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

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
                        self.requests[req["id"]] = Request(**req)
        except Exception as e:
            logger.error(f"Failed to load requests: {e}")
            self.requests = {}
    
    def _save_requests(self):
        """Save requests to file."""
        try:
            data = [
                {
                    "id": req.id,
                    "message": req.message,
                    "timestamp": req.timestamp,
                    "status": req.status,
                    "response": req.response,
                    "error": req.error
                }
                for req in self.requests.values()
            ]
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
        error: Optional[str] = None
    ):
        """Update request status.
        
        Args:
            request_id: Request ID
            status: New status
            response: Response text
            error: Error message
        """
        if request_id in self.requests:
            request = self.requests[request_id]
            request.status = status
            request.response = response
            request.error = error
            self._save_requests()
    
    def get_pending_requests(self) -> List[Request]:
        """Get pending requests.
        
        Returns:
            List of pending requests
        """
        return [
            req for req in self.requests.values()
            if req.status == "pending"
        ]
    
    def clear_completed(self):
        """Clear completed requests."""
        self.requests = {
            id: req for id, req in self.requests.items()
            if req.status == "pending"
        }
        self._save_requests() 