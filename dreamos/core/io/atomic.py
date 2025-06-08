"""
Atomic Operations Module

Atomic file operations for the Dream.OS system.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

def safe_read(file_path: str) -> str:
    """Read a file safely using a temporary file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File contents as a string
    """
    with open(file_path) as f:
        return f.read()
        
def safe_write(file_path: str, content: str) -> None:
    """Write to a file safely using a temporary file.
    
    Args:
        file_path: Path to the file
        content: Content to write
    """
    # Create a temporary file in the same directory
    dir_name = os.path.dirname(file_path)
    with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, delete=False) as tf:
        temp_path = tf.name
        tf.write(content)
        
    # Atomic rename
    os.replace(temp_path, file_path) 
