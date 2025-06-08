"""Cleanup utilities for social media operations."""

import logging
import os
import shutil
from typing import List, Optional

logger = logging.getLogger(__name__)

def cleanup_temp_files(directory: str, pattern: Optional[str] = None) -> List[str]:
    """Clean up temporary files in the specified directory.
    
    Args:
        directory: Directory to clean up
        pattern: Optional pattern to match files (e.g. "*.tmp")
        
    Returns:
        List of cleaned up file paths
    """
    cleaned_files = []
    try:
        if not os.path.exists(directory):
            return cleaned_files
            
        for filename in os.listdir(directory):
            if pattern and not filename.endswith(pattern):
                continue
                
            filepath = os.path.join(directory, filename)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    cleaned_files.append(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                    cleaned_files.append(filepath)
            except Exception as e:
                logger.error(f"Error cleaning up {filepath}: {e}")
                
        return cleaned_files
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return cleaned_files

def cleanup_old_logs(log_dir: str, max_age_days: int = 30) -> List[str]:
    """Clean up old log files.
    
    Args:
        log_dir: Directory containing log files
        max_age_days: Maximum age of logs in days
        
    Returns:
        List of cleaned up log file paths
    """
    cleaned_files = []
    try:
        if not os.path.exists(log_dir):
            return cleaned_files
            
        current_time = os.path.getmtime(log_dir)
        for filename in os.listdir(log_dir):
            if not filename.endswith('.log'):
                continue
                
            filepath = os.path.join(log_dir, filename)
            try:
                file_time = os.path.getmtime(filepath)
                age_days = (current_time - file_time) / (24 * 3600)
                
                if age_days > max_age_days:
                    os.remove(filepath)
                    cleaned_files.append(filepath)
            except Exception as e:
                logger.error(f"Error cleaning up log {filepath}: {e}")
                
        return cleaned_files
    except Exception as e:
        logger.error(f"Error during log cleanup: {e}")
        return cleaned_files 
