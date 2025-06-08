import os
from pathlib import Path

class Config:
    def __init__(self):
        self._log_dir = None
        self.log_dir = "logs"  # Default value

    @property
    def log_dir(self) -> str:
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value: str):
        # Convert to absolute path if relative
        if not os.path.isabs(value):
            value = os.path.abspath(value)
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(value, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Failed to create log directory: {e}")
        
        self._log_dir = value 
