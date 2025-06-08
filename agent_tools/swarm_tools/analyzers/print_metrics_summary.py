"""
Log Metrics Summary Tool
-----------------------
Prints a beautiful summary of log metrics for demo/showcase purposes.
"""

import json
from pathlib import Path
from datetime import datetime
import sys
from typing import Dict, Any
import argparse

def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"

def print_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Print a beautiful summary of log metrics.
    
    Args:
        metrics: Dictionary of metrics from LogMetrics.get_metrics()
    """
    print("\n=== 📊 Log Metrics Summary ===\n")
    
    # Overall stats
    print("📈 Overall Stats:")
    print(f"  • Total Logs: {metrics['total_logs']:,}")
    print(f"  • Uptime: {format_duration(metrics['uptime'])}")
    print(f"  • Error Rate: {metrics['error_count'] / max(metrics['total_logs'], 1) * 100:.1f}%")
    
    # Platform breakdown
    print("\n🌐 Platform Breakdown:")
    for platform, count in sorted(metrics['platform_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {platform}: {count:,} logs")
    
    # Level distribution
    print("\n📊 Log Level Distribution:")
    for level, count in sorted(metrics['level_counts'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / max(metrics['total_logs'], 1) * 100
        print(f"  • {level}: {count:,} ({percentage:.1f}%)")
    
    # Status breakdown
    print("\n🔄 Status Breakdown:")
    for status, count in sorted(metrics['status_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {status}: {count:,}")
    
    # Error details
    if metrics['error_count'] > 0:
        print("\n⚠️ Error Details:")
        print(f"  • Total Errors: {metrics['error_count']:,}")
        if metrics['last_error']:
            print(f"  • Last Error: {metrics['last_error']}")
            if metrics['last_error_time']:
                error_time = datetime.fromtimestamp(metrics['last_error_time'])
                print(f"  • Last Error Time: {error_time.isoformat()}")
    
    # Rotation stats
    if 'rotation_count' in metrics:
        print("\n🔄 Rotation Stats:")
        print(f"  • Total Rotations: {metrics['rotation_count']:,}")
        if metrics['last_rotation']:
            print(f"  • Last Rotation: {metrics['last_rotation']}")
    
    print("\n=== End of Metrics Summary ===\n")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Print a summary of log metrics")
    parser.add_argument("--metrics-file", type=str, help="Path to metrics JSON file")
    parser.add_argument("--log-dir", type=str, help="Path to log directory")
    args = parser.parse_args()
    
    # Try to load metrics from file if provided
    if args.metrics_file:
        try:
            with open(args.metrics_file) as f:
                metrics = json.load(f)
        except Exception as e:
            print(f"Error loading metrics file: {e}", file=sys.stderr)
            sys.exit(1)
    # Otherwise try to load from log directory
    elif args.log_dir:
        try:
            log_dir = Path(args.log_dir)
            metrics_file = log_dir / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    metrics = json.load(f)
            else:
                print(f"No metrics file found in {log_dir}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error loading metrics from log directory: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Please provide either --metrics-file or --log-dir", file=sys.stderr)
        sys.exit(1)
    
    print_metrics_summary(metrics)

if __name__ == "__main__":
    main() 
