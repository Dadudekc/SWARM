"""
Log Cleanup Module
-----------------
Handles log rotation and cleanup.
"""

import os
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def cleanup_old_logs(log_dir: str, max_age_days: int = 30) -> None:
    """Clean up log files older than max_age_days.
    
    Args:
        log_dir: Directory containing log files
        max_age_days: Maximum age of logs in days
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for log_file in Path(log_dir).glob('*.log'):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                # Delete if older than cutoff
                if mtime < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")

def rotate_log(log_file: str, max_size_mb: int = 10, backup_count: int = 5) -> None:
    """Rotate a log file if it exceeds max_size_mb.
    
    Args:
        log_file: Path to the log file
        max_size_mb: Maximum size in MB before rotation
        backup_count: Number of backup files to keep
    """
    try:
        if not os.path.exists(log_file):
            return
            
        # Check file size
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        if size_mb < max_size_mb:
            return
            
        # Rotate existing backups
        for i in range(backup_count - 1, 0, -1):
            old = f"{log_file}.{i}"
            new = f"{log_file}.{i + 1}"
            if os.path.exists(old):
                if os.path.exists(new):
                    os.remove(new)
                os.rename(old, new)
                
        # Rotate current log
        if os.path.exists(f"{log_file}.1"):
            os.remove(f"{log_file}.1")
        os.rename(log_file, f"{log_file}.1")
        
        # Create new empty log file
        open(log_file, 'a').close()
        
        logger.info(f"Rotated log file: {log_file}")
    except Exception as e:
        logger.error(f"Error rotating log file {log_file}: {e}")

def compress_old_logs(log_dir: str, compress_after_days: int = 7) -> None:
    """Compress log files older than compress_after_days.
    
    Args:
        log_dir: Directory containing log files
        compress_after_days: Age in days after which to compress
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=compress_after_days)
        
        for log_file in Path(log_dir).glob('*.log.*'):
            try:
                # Skip already compressed files
                if log_file.suffix == '.gz':
                    continue
                    
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                # Compress if older than cutoff
                if mtime < cutoff_date:
                    import gzip
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    log_file.unlink()
                    logger.info(f"Compressed old log file: {log_file}")
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error compressing logs: {e}") 