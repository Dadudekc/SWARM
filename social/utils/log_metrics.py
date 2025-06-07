"""Log metrics tracking and analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class LogMetrics:
    """Metrics for log analysis and tracking."""
    
    total_logs: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    last_log_time: Optional[datetime] = None
    log_sources: Dict[str, int] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    
    def add_log(self, level: str, source: str, error_type: Optional[str] = None) -> None:
        """Add a log entry to metrics."""
        self.total_logs += 1
        self.last_log_time = datetime.now()
        
        # Update level counts
        if level == "ERROR":
            self.error_count += 1
        elif level == "WARNING":
            self.warning_count += 1
        elif level == "INFO":
            self.info_count += 1
        elif level == "DEBUG":
            self.debug_count += 1
            
        # Update source counts
        self.log_sources[source] = self.log_sources.get(source, 0) + 1
        
        # Update error type counts if applicable
        if error_type:
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
            
    def get_error_rate(self) -> float:
        """Calculate the error rate as a percentage."""
        if self.total_logs == 0:
            return 0.0
        return (self.error_count / self.total_logs) * 100
    
    def get_source_distribution(self) -> Dict[str, float]:
        """Get the distribution of logs by source as percentages."""
        if self.total_logs == 0:
            return {}
        return {
            source: (count / self.total_logs) * 100
            for source, count in self.log_sources.items()
        }
    
    def get_error_type_distribution(self) -> Dict[str, float]:
        """Get the distribution of errors by type as percentages."""
        if self.error_count == 0:
            return {}
        return {
            error_type: (count / self.error_count) * 100
            for error_type, count in self.error_types.items()
        }
    
    def reset(self) -> None:
        """Reset all metrics to their initial state."""
        self.total_logs = 0
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0
        self.debug_count = 0
        self.last_log_time = None
        self.log_sources.clear()
        self.error_types.clear() 