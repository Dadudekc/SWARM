"""
Response Processor Implementation
------------------------------
Processes and validates responses in the system.
"""

from typing import Dict, Any, Optional, List
import logging
import json
from pathlib import Path
from .base import BaseProcessor
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseProcessor(BaseProcessor):
    """Processes and validates responses."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the response processor.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.required_fields = config.get('required_fields', ['status', 'data'])
        self.valid_statuses = config.get('valid_statuses', ['success', 'error'])
        self.max_retries = config.get('max_retries', 3)
        
        # Initialize metrics
        self.metrics_path = Path("data/metrics")
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self._init_metrics()
        
    def _init_metrics(self):
        """Initialize metrics file."""
        metrics_file = self.metrics_path / "bridge_metrics.json"
        if not metrics_file.exists():
            metrics = {
                "processed_messages": 0,
                "failed_messages": 0,
                "total_response_time": 0,
                "last_processed": None
            }
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
    def _update_metrics(self, success: bool, response_time: float):
        """Update metrics.
        
        Args:
            success: Whether message was processed successfully
            response_time: Time taken to process message
        """
        metrics_file = self.metrics_path / "bridge_metrics.json"
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
                
            if success:
                metrics["processed_messages"] += 1
            else:
                metrics["failed_messages"] += 1
                
            metrics["total_response_time"] += response_time
            metrics["last_processed"] = datetime.now().isoformat()
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
        
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate a response.
        
        Args:
            data: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.error("Response must be a dictionary")
            return False
            
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Check status
        if 'status' in data and data['status'] not in self.valid_statuses:
            logger.error(f"Invalid status: {data['status']}")
            return False
            
        return True
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            data: Response to process
            
        Returns:
            Processed response
        """
        start_time = datetime.now()
        
        if not await self.validate(data):
            self._update_metrics(success=False, response_time=0)
            raise ValueError("Invalid response")
            
        try:
            # Add processing metadata
            processed = data.copy()
            processed['processed_at'] = datetime.now().isoformat()
            processed['processor'] = self.__class__.__name__
            
            # Handle retries if needed
            if data.get('status') == 'error' and data.get('retry_count', 0) < self.max_retries:
                processed['retry_count'] = data.get('retry_count', 0) + 1
                processed['should_retry'] = True
            else:
                processed['should_retry'] = False
                
            # Increment processed count
            self.processed_count += 1
            
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(success=True, response_time=response_time)
            
            return processed
            
        except Exception as e:
            # Update metrics for failure
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(success=False, response_time=response_time)
            await self.handle_error(e, {'response': data})
            raise
            
    async def handle_retry(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle retry logic for failed responses.
        
        Args:
            response: Response to retry
            
        Returns:
            Updated response
        """
        if response.get('status') == 'error' and response.get('retry_count', 0) < self.max_retries:
            response['retry_count'] = response.get('retry_count', 0) + 1
            response['should_retry'] = True
            logger.info(f"Retrying response (attempt {response['retry_count']})")
        else:
            response['should_retry'] = False
            logger.error("Max retries exceeded")
            
        return response 