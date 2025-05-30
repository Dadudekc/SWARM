"""
Command metrics tracking and reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

class CommandMetrics:
    """Track and report command usage metrics."""
    
    def __init__(self, metrics_dir: Optional[Path] = None):
        """Initialize command metrics.
        
        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = metrics_dir or Path("metrics")
        self.metrics_dir.mkdir(exist_ok=True)
        self.command_counts: Dict[str, int] = {}
        self.last_reset = datetime.now()
        
    def track_command(self, command_name: str) -> None:
        """Track a command execution.
        
        Args:
            command_name: Name of the command executed
        """
        self.command_counts[command_name] = self.command_counts.get(command_name, 0) + 1
        
    def get_command_stats(self) -> Dict[str, int]:
        """Get current command statistics.
        
        Returns:
            Dictionary of command names to execution counts
        """
        return self.command_counts.copy()
        
    def reset_stats(self) -> None:
        """Reset command statistics."""
        self.command_counts.clear()
        self.last_reset = datetime.now()
        
    def save_metrics(self) -> None:
        """Save current metrics to file."""
        metrics_file = self.metrics_dir / f"command_metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metrics_file, "w") as f:
            json.dump({
                "last_reset": self.last_reset.isoformat(),
                "command_counts": self.command_counts
            }, f, indent=2)
            
    def load_metrics(self) -> None:
        """Load metrics from most recent file."""
        metrics_files = sorted(self.metrics_dir.glob("command_metrics_*.json"))
        if metrics_files:
            with open(metrics_files[-1]) as f:
                data = json.load(f)
                self.last_reset = datetime.fromisoformat(data["last_reset"])
                self.command_counts = data["command_counts"] 