"""
Base Metrics Module
-----------------
Core metrics functionality and base classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

class BaseMetrics:
    """Base class for all metrics implementations."""
    
    def __init__(self, name: str, metrics_dir: Optional[Path] = None):
        """Initialize metrics.
        
        Args:
            name: Name of this metrics instance
            metrics_dir: Optional directory to persist metrics
        """
        self.name = name
        self.start_time = datetime.now()
        self.metrics_dir = metrics_dir or Path("metrics")
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}
        
    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Metric name
            value: Amount to increment by
            tags: Optional tags for the metric
        """
        key = self._get_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value
        self._save()
        
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric.
        
        Args:
            name: Metric name
            value: Current value
            tags: Optional tags for the metric
        """
        key = self._get_key(name, tags)
        self._gauges[key] = value
        self._save()
        
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value.
        
        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for the metric
        """
        key = self._get_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._save()
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics.
        
        Returns:
            Dictionary containing all metrics
        """
        return {
            'name': self.name,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'counters': self._counters,
            'gauges': self._gauges,
            'histograms': {
                k: {
                    'count': len(v),
                    'sum': sum(v),
                    'min': min(v),
                    'max': max(v),
                    'avg': sum(v) / len(v)
                }
                for k, v in self._histograms.items()
            }
        }
        
    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._save()
        
    def _get_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Get a unique key for a metric with tags.
        
        Args:
            name: Metric name
            tags: Optional tags
            
        Returns:
            Unique key string
        """
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
        
    def _save(self) -> None:
        """Save metrics to disk."""
        try:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            metrics_file = self.metrics_dir / f"{self.name}_metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(self.get_metrics(), f, indent=2, default=str)
        except Exception as e:
            # Log error but don't fail
            print(f"Failed to save metrics: {e}") 