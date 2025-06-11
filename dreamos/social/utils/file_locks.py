"""
File Locking Module
------------------
Handles platform-specific file locking mechanisms.
"""

import os
import logging
import platform as platform_module
from typing import ContextManager, TextIO
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Import appropriate locking mechanism based on platform
if platform_module.system() == 'Windows':
    import msvcrt
    import win32file
    import win32con
    import win32api
    import pywintypes
    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # Shared lock not used
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    LOCK_UN = 0  # Unlock not needed, handled by closing file
    
    # Try to import win32security, but don't fail if not available
    try:
        import win32security
        import ntsecuritycon as con
        HAS_WIN32SECURITY = True
    except ImportError:
        logger.warning("win32security not available, will use basic Windows permissions")
        HAS_WIN32SECURITY = False
else:
    import fcntl
    LOCK_EX = fcntl.LOCK_EX
    LOCK_SH = fcntl.LOCK_SH
    LOCK_NB = fcntl.LOCK_NB
    LOCK_UN = fcntl.LOCK_UN
    HAS_WIN32SECURITY = False

def get_file_lock(log_file: str) -> ContextManager[TextIO]:
    """Get a file lock for the specified log file.
    
    Args:
        log_file: Path to the log file
        
    Returns:
        Context manager that yields a file handle with appropriate locking
    """
    @contextmanager
    def lock_context():
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Open file in append mode
            with open(log_file, 'a') as f:
                yield f
        except Exception as e:
            logger.error(f"Error getting file lock: {e}")
            raise

    return lock_context()

def ensure_log_dir(log_dir: str) -> None:
    """Ensure the log directory exists with proper permissions.
    
    Args:
        log_dir: Path to the log directory
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
        
        if HAS_WIN32SECURITY:
            # Set Windows-specific permissions
            security_info = win32security.GetFileSecurity(
                log_dir, 
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = security_info.GetSecurityDescriptorDacl()
            
            # Add full control for the current user
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32con.TOKEN_QUERY
                ),
                win32security.TokenUser
            )[0]
            
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                win32con.GENERIC_ALL,
                user_sid
            )
            
            security_info.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                log_dir,
                win32security.DACL_SECURITY_INFORMATION,
                security_info
            )
    except Exception as e:
        logger.error(f"Error setting up log directory: {e}")
        raise 