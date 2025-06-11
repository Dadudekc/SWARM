"""
Bridge Processor
-------------
Bridge-specific processor implementation.
"""

from typing import Dict, Any, Optional
from dreamos.core.shared.processors.base import BaseProcessor

class BridgeProcessor(BaseProcessor):
    """Bridge-specific processor implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge processor.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.bridge_config = config.get('bridge_config', {}) if config else {}
        self._metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'last_error': None
        }
        
    @property
    def total_processed(self) -> int:
        """Get total processed count."""
        return self._metrics['total_processed']
        
    @property
    def total_failed(self) -> int:
        """Get total failed count."""
        return self._metrics['total_failed']
        
    def _update_metrics(self, success: bool, error: Optional[Exception] = None) -> None:
        """Update processor metrics.
        
        Args:
            success: Whether operation succeeded
            error: Optional error that occurred
        """
        if success:
            self._metrics['total_processed'] += 1
        else:
            self._metrics['total_failed'] += 1
            self._metrics['last_error'] = str(error) if error else None
            
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process bridge data.
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
        """
        if not await self.validate(data):
            self._update_metrics(False, ValueError("Invalid bridge data"))
            raise ValueError("Invalid bridge data")
            
        try:
            # Add bridge-specific processing
            processed = data.copy()
            processed['bridge_processed'] = True
            processed['bridge_config'] = self.bridge_config
            
            # Update metrics for successful processing
            self._update_metrics(True)
            return processed
            
        except Exception as e:
            self._update_metrics(False, e)
            await self.handle_error(e, data)
            raise
            
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate bridge data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['type', 'content']
        return all(field in data for field in required_fields)
        
    async def handle_error(self, error: Exception, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an error.
        
        Args:
            error: Error that occurred
            data: Data that caused error
            
        Returns:
            Error response
        """
        return {
            'error': str(error),
            'data': data,
            'bridge_processed': False
        }
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics.
        
        Returns:
            Metrics dictionary
        """
        metrics = super().get_metrics()
        metrics.update(self._metrics)
        metrics.update({
            'bridge_config': self.bridge_config
        })
        return metrics 