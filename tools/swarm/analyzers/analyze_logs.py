"""
Log Analyzer CLI
---------------
Command-line tool for analyzing agent logs.
"""

import argparse
from pathlib import Path
from collections import Counter
import re
import json
from datetime import datetime, timedelta
import shutil
from typing import List, Dict, Any, Optional

LOG_DIR = Path("logs/agent_loop")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze agent logs.")
    parser.add_argument("--agent", required=True, help="Agent ID to analyze")
    parser.add_argument("--level", default="info", choices=["debug", "info", "warning", "error"],
                      help="Log level to analyze")
    parser.add_argument("--summary", action="store_true", help="Generate summary")
    parser.add_argument("--export", choices=["json", "md"], help="Export format")
    parser.add_argument("--clear", action="store_true", help="Clear old logs")
    parser.add_argument("--rotate", action="store_true", help="Rotate log files")
    parser.add_argument("--days", type=int, default=7, help="Days of logs to keep")
    return parser.parse_args()

def parse_log_file(agent: str, level: str) -> List[Dict[str, Any]]:
    """Parse log file for an agent.
    
    Args:
        agent: Agent ID
        level: Log level
        
    Returns:
        List of log entries
    """
    log_file = LOG_DIR / f"{agent}_loop_{level}.log"
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return []

    entries = []
    with open(log_file) as f:
        for line in f:
            timestamp_match = re.match(r"\[(.*?)\]", line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                msg = line[timestamp_match.end():].strip()
                entries.append({
                    "timestamp": timestamp,
                    "message": msg,
                    "level": level
                })
    return entries

def summarize(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary of log entries.
    
    Args:
        entries: List of log entries
        
    Returns:
        Summary dictionary
    """
    # Count errors
    errors = [e["message"] for e in entries if "error" in e["message"].lower()]
    error_freq = Counter(errors)
    
    # Find idle gaps
    gaps = []
    last_time = None
    for e in entries:
        try:
            t = datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S")
            if last_time and (t - last_time).seconds > 60:
                gaps.append((last_time, t))
            last_time = t
        except ValueError:
            continue
    
    # Count by level
    level_counts = Counter(e["level"] for e in entries)
    
    return {
        "total_entries": len(entries),
        "level_counts": dict(level_counts),
        "unique_errors": dict(error_freq),
        "idle_gaps": [(str(a), str(b)) for a, b in gaps],
        "first_entry": entries[0]["timestamp"] if entries else None,
        "last_entry": entries[-1]["timestamp"] if entries else None
    }

def export(data: Dict[str, Any], fmt: str):
    """Export summary in specified format.
    
    Args:
        data: Summary data
        fmt: Export format (json/md)
    """
    if fmt == "json":
        print(json.dumps(data, indent=2))
    elif fmt == "md":
        print("# Log Summary\n")
        print(f"- Total Entries: {data['total_entries']}")
        
        print("\n## Level Distribution")
        for level, count in data["level_counts"].items():
            print(f"- {level.upper()}: {count}")
        
        print("\n## Frequent Errors")
        for err, count in data["unique_errors"].items():
            print(f"- `{err}`: {count}")
        
        print("\n## Idle Gaps > 60s")
        for a, b in data["idle_gaps"]:
            print(f"- {a} → {b}")
        
        print("\n## Time Range")
        print(f"- First Entry: {data['first_entry']}")
        print(f"- Last Entry: {data['last_entry']}")

def clear_logs(agent: str, days: int):
    """Clear old log files.
    
    Args:
        agent: Agent ID
        days: Days of logs to keep
    """
    cutoff = datetime.now() - timedelta(days=days)
    
    for level in ["debug", "info", "warning", "error"]:
        log_file = LOG_DIR / f"{agent}_loop_{level}.log"
        if log_file.exists():
            # Create backup
            backup = log_file.with_suffix(f".{cutoff.strftime('%Y%m%d')}.log")
            shutil.copy2(log_file, backup)
            
            # Clear current log
            with open(log_file, "w") as f:
                f.write(f"# Log cleared at {datetime.now()}\n")
                f.write(f"# Previous logs backed up to {backup.name}\n\n")

def rotate_logs(agent: str):
    """Rotate log files.
    
    Args:
        agent: Agent ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for level in ["debug", "info", "warning", "error"]:
        log_file = LOG_DIR / f"{agent}_loop_{level}.log"
        if log_file.exists():
            # Create rotated file
            rotated = log_file.with_suffix(f".{timestamp}.log")
            shutil.copy2(log_file, rotated)
            
            # Clear current log
            with open(log_file, "w") as f:
                f.write(f"# Log rotated at {datetime.now()}\n")
                f.write(f"# Previous logs in {rotated.name}\n\n")

def main():
    """Main entry point."""
    args = parse_args()
    
    # Handle maintenance commands
    if args.clear:
        clear_logs(args.agent, args.days)
        print(f"Cleared logs for {args.agent}, keeping last {args.days} days")
        return
        
    if args.rotate:
        rotate_logs(args.agent)
        print(f"Rotated logs for {args.agent}")
        return
    
    # Analyze logs
    entries = parse_log_file(args.agent, args.level)
    if not entries:
        print(f"No logs found for {args.agent} at {args.level} level")
        return
        
    if args.summary:
        data = summarize(entries)
        if args.export:
            export(data, args.export)
        else:
            print(json.dumps(data, indent=2))
    else:
        # Print raw entries
        for entry in entries:
            print(f"[{entry['timestamp']}] {entry['message']}")

if __name__ == "__main__":
    main() 
