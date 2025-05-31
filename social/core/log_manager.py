"""
Log Manager Module
----------------
Provides functionality for managing logs.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class LogConfig:
    """Configuration for log management."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.platforms = {}
        
    def add_platform(self, platform: str, log_file: str):
        """Add a platform and its log file."""
        self.platforms[platform] = log_file

class LogManager:
    """Manages logging operations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.config = LogConfig()
        self.logs = {}
        self._initialized = True
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.config.log_dir):
            os.makedirs(self.config.log_dir)
            
    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance."""
        cls._instance = None
        
    def write_log(self, platform: str, level: str, message: str):
        """Write a log entry."""
        if platform not in self.logs:
            self.logs[platform] = []
            
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        self.logs[platform].append(entry)
        
        # Write to file
        log_file = os.path.join(self.config.log_dir, f"{platform}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{entry['timestamp']} [{level:8}] {message}\n")
            
    def get_logs(self, platform: str) -> List[Dict]:
        """Get logs for a platform."""
        return self.logs.get(platform, [])
        
    def clear_logs(self, platform: Optional[str] = None):
        """Clear logs for a platform or all platforms."""
        if platform:
            if platform in self.logs:
                self.logs[platform] = []
                log_file = os.path.join(self.config.log_dir, f"{platform}.log")
                if os.path.exists(log_file):
                    os.remove(log_file)
        else:
            self.logs.clear()
            for file in os.listdir(self.config.log_dir):
                if file.endswith(".log"):
                    os.remove(os.path.join(self.config.log_dir, file))
                    
    def cleanup(self):
        """Clean up log files."""
        for file in os.listdir(self.config.log_dir):
            if file.endswith(".log"):
                os.remove(os.path.join(self.config.log_dir, file)) 