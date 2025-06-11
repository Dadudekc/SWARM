"""
Handler Utilities
---------------
Shared utilities for handler operations across the system.
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Awaitable, Union
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

async def safe_watch_file(
    file_path: Path,
    process_callback: Callable[[Path], Awaitable[None]],
    error_callback: Optional[Callable[[Exception, Path], Awaitable[None]]] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> bool:
    """Safely watch and process a file with retries.
    
    Args:
        file_path: Path to watch
        process_callback: Async callback to process the file
        error_callback: Optional callback for error handling
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        bool: True if processing succeeded
    """
    for attempt in range(max_retries):
        try:
            await process_callback(file_path)
            return True
        except Exception as e:
            if error_callback:
                await error_callback(e, file_path)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to process {file_path} after {max_retries} attempts: {e}")
                return False

def structured_log(
    platform: str,
    status: str,
    message: str,
    tags: Optional[list[str]] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a structured log entry.
    
    Args:
        platform: Platform/component name
        status: Status string (e.g. 'success', 'error')
        message: Log message
        tags: Optional list of tags
        details: Optional additional details
        
    Returns:
        Dict containing structured log data
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'platform': platform,
        'status': status,
        'message': message,
        'tags': tags or []
    }
    if details:
        log_entry['details'] = details
    return log_entry

async def standard_result_wrapper(
    operation: Callable[..., Awaitable[Any]],
    *args: Any,
    success_message: str = "Operation completed successfully",
    error_message: str = "Operation failed",
    **kwargs: Any
) -> Dict[str, Any]:
    """Wrap an async operation with standard result handling.
    
    Args:
        operation: Async operation to execute
        *args: Positional arguments for operation
        success_message: Message for successful execution
        error_message: Message for failed execution
        **kwargs: Keyword arguments for operation
        
    Returns:
        Dict containing operation result and metadata
    """
    try:
        result = await operation(*args, **kwargs)
        return {
            'success': True,
            'message': success_message,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"{error_message}: {str(e)}",
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def safe_json_operation(
    file_path: Union[str, Path],
    operation: Callable[[Dict[str, Any]], Awaitable[None]],
    default_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Safely perform a JSON file operation with error handling.
    
    Args:
        file_path: Path to JSON file
        operation: Async operation to perform on JSON data
        default_data: Default data if file doesn't exist
        
    Returns:
        bool: True if operation succeeded
    """
    try:
        # Ensure path is Path object
        path = Path(file_path)
        
        # Read existing data or use default
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            data = default_data or {}
            
        # Perform operation
        await operation(data)
        
        # Write back to file
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
        return True
        
    except Exception as e:
        logger.error(f"Error in JSON operation on {file_path}: {e}")
        return False 