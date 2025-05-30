"""
Log Writer Module
----------------
Handles writing log entries to files in various formats.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import json
from enum import Enum
from dataclasses import dataclass
import os

class LogLevel(Enum):
    """Log levels for entries."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Represents a single log entry."""
    platform: str
    status: str
    message: str
    level: str
    timestamp: str
    tags: List[str]
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class LogWriter:
    """Handles writing log entries to files."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize LogWriter.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def write_log(self, entry: Union[LogEntry, Dict[str, Any]], format: str = "json") -> None:
        """Write a log entry to file.
        
        Args:
            entry: LogEntry or dict to write
            format: Output format ("json" or "text")
        """
        # Convert dict to LogEntry if needed
        if isinstance(entry, dict):
            entry = LogEntry(
                platform=entry["platform"],
                status=entry["status"],
                message=entry["message"],
                level=entry["level"],
                timestamp=entry.get("timestamp", datetime.now().isoformat()),
                tags=entry.get("tags", []),
                metadata=entry.get("metadata"),
                error=entry.get("error")
            )
        
        # Create platform-specific log file
        log_file = self.log_dir / f"{entry.platform}_operations.json"
        
        # Convert entry to dict
        log_dict = {
            "timestamp": entry.timestamp,
            "platform": entry.platform,
            "status": entry.status,
            "level": entry.level,
            "message": entry.message,
            "tags": entry.tags
        }
        
        if entry.metadata:
            log_dict["metadata"] = entry.metadata
        if entry.error:
            log_dict["error"] = entry.error
            
        # Write to file based on format
        if format == "json":
            # Read existing logs if file exists
            existing_logs = []
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        existing_logs = json.load(f)
                except json.JSONDecodeError:
                    existing_logs = []
            
            # Append new log
            existing_logs.append(log_dict)
            
            # Write back to file
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(existing_logs, f, indent=2)
        else:  # text format
            with open(log_file.with_suffix(".log"), "a", encoding="utf-8") as f:
                f.write(f"{log_dict['timestamp']} [{log_dict['level']}] {log_dict['message']}\n")

def write_json_log(platform: str, status: str, message: str, level: str = "INFO", 
                  tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[str] = None) -> None:
    """Helper function to write a log entry.
    
    Args:
        platform: Platform name
        status: Status of the operation
        message: Log message
        level: Log level (default: INFO)
        tags: Optional list of tags
        metadata: Optional metadata dictionary
        error: Optional error message
    """
    writer = LogWriter()
    entry = LogEntry(
        platform=platform,
        status=status,
        message=message,
        level=level,
        timestamp=datetime.now().isoformat(),
        tags=tags or [],
        metadata=metadata,
        error=error
    )
    writer.write_log(entry) 