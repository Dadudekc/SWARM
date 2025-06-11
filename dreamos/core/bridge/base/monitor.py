"""
Base Monitor Interface
------------------
Defines the interface that all bridge monitors must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
import json
from pathlib import Path

class BaseMonitor(ABC):
    """Base class for all bridge monitors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.metrics = {}
        self.start_time = datetime.now()
        
    @abstractmethod
    async def record_metric(self, name: str, value: Any) -> None:
        """Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            Metrics dictionary
        """
        pass
        
    @abstractmethod
    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        pass
        
    @abstractmethod
    async def save_metrics(self, file_path: Path) -> None:
        """Save metrics to file.
        
        Args:
            file_path: Path to save metrics
        """
        pass
        
    @abstractmethod
    async def load_metrics(self, file_path: Path) -> None:
        """Load metrics from file.
        
        Args:
            file_path: Path to load metrics from
        """
        pass

class BridgeMonitor(BaseMonitor):
    """Bridge-specific monitor implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.running = False
        self.metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'processing_time': 0.0,
            'last_error': None,
            'last_success': None
        }
        
    def start(self):
        """Start the bridge monitor.
        
        This method initializes monitoring and sets the running state.
        It can be extended to start background threads or polling.
        """
        if self.running:
            self.logger.warning("Bridge monitor is already running")
            return
            
        self.running = True
        self.logger.info("Bridge monitor started")
        
    def stop(self):
        """Stop the bridge monitor.
        
        This method performs cleanup and resets the running state.
        It can be extended to stop background threads or polling.
        """
        if not self.running:
            self.logger.warning("Bridge monitor is not running")
            return
            
        self.running = False
        self.metrics.clear()
        self.logger.info("Bridge monitor stopped")
        
    async def record_metric(self, name: str, value: Any) -> None:
        """Record a bridge metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        if not self.running:
            self.logger.warning(f"Cannot record metric '{name}' - monitor is not running")
            return
            
        if name not in self.metrics:
            self.metrics[name] = 0
            
        if isinstance(value, (int, float)):
            self.metrics[name] += value
        else:
            self.metrics[name] = value
            
        # Update timestamps
        if name == 'total_processed':
            self.metrics['last_success'] = datetime.utcnow().isoformat()
        elif name == 'total_failed':
            self.metrics['last_error'] = datetime.utcnow().isoformat()
            
        self.logger.debug(f"Recorded metric: {name}={value}")
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get all bridge metrics.
        
        Returns:
            Metrics dictionary
        """
        metrics = self.metrics.copy()
        metrics['uptime'] = (datetime.now() - self.start_time).total_seconds()
        return metrics
        
    async def reset_metrics(self) -> None:
        """Reset all bridge metrics."""
        self.metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'processing_time': 0.0,
            'last_error': None,
            'last_success': None
        }
        self.start_time = datetime.now()
        
    async def save_metrics(self, file_path: Path) -> None:
        """Save bridge metrics to file.
        
        Args:
            file_path: Path to save metrics
        """
        metrics = await self.get_metrics()
        with open(file_path, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    async def load_metrics(self, file_path: Path) -> None:
        """Load bridge metrics from file.
        
        Args:
            file_path: Path to load metrics from
        """
        with open(file_path, 'r') as f:
            metrics = json.load(f)
            
        # Update metrics
        for name, value in metrics.items():
            if name != 'uptime':  # Skip uptime as it's calculated
                self.metrics[name] = value
                
        # Update start time based on uptime
        if 'uptime' in metrics:
            self.start_time = datetime.now() - datetime.timedelta(seconds=metrics['uptime'])

    async def update_metrics(self, success: bool, error: Optional[Exception] = None) -> None:
        """Update monitor metrics.
        
        Args:
            success: Whether operation succeeded
            error: Optional error that occurred
        """
        if success:
            self.metrics['total_processed'] += 1
        else:
            self.metrics['total_failed'] += 1
            self.metrics['last_error'] = str(error) if error else None
            
    async def reset(self) -> None:
        """Reset monitor state."""
        self.metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'processing_time': 0.0,
            'last_error': None,
            'last_success': None
        }
        self.start_time = datetime.now() 