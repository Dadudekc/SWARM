"""
Command metrics tracking and reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from dreamos.core.utils.file_utils import (
    ensure_dir,
    safe_write,
    safe_read,
    read_json,
    write_json,
    load_json,
    save_json
)

class CommandMetrics:
    """Track and report command usage metrics."""
    
    def __init__(self, metrics_dir: Optional[Path] = None):
        """Initialize command metrics.
        
        Args:
            metrics_dir: Directory to store metrics files
        """
        self.metrics_dir = metrics_dir or Path("metrics")
        ensure_dir(str(self.metrics_dir))
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
        try:
            save_json(str(metrics_file), {
                "last_reset": self.last_reset.isoformat(),
                "command_counts": self.command_counts
            })
            
            # Rotate old metrics files (keep last 30 days)
            rotate_file(str(metrics_file), max_files=30)
        except FileOpsError as e:
            print(f"Error saving metrics: {e}")
            
    def load_metrics(self) -> None:
        """Load metrics from most recent file."""
        metrics_files = sorted(self.metrics_dir.glob("command_metrics_*.json"))
        if metrics_files:
            try:
                data = load_json(str(metrics_files[-1]))
                self.last_reset = datetime.fromisoformat(data["last_reset"])
                self.command_counts = data["command_counts"]
            except FileOpsError as e:
                print(f"Error loading metrics: {e}")

def save_metrics(metrics_file: str, metrics: Dict) -> None:
    """Save metrics to file."""
    save_json(str(metrics_file), metrics)

def load_metrics(metrics_files: List[Path]) -> Dict:
    """Load metrics from file."""
    data = load_json(str(metrics_files[-1]))
    return data if data else {} 