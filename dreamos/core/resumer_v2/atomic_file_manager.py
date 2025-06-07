"""
Atomic File Manager

Provides atomic file operations with backup support and error recovery.
"""

import os
import json
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AtomicFileManager:
    """Manages atomic file operations with backup support."""
    
    def __init__(self, file_path: Path, max_retries: int = 3):
        """Initialize the atomic file manager.
        
        Args:
            file_path: Path to the managed file
            max_retries: Maximum number of retry attempts for failed operations
        """
        self.file_path = Path(file_path)
        self._lock = asyncio.Lock()
        self._backup_path = self.file_path.with_suffix('.json.bak')
        self._temp_path = self.file_path.with_suffix('.json.tmp')
        self.max_retries = max_retries
        
    async def atomic_write(self, data: Dict[str, Any]) -> bool:
        """Write data to file atomically with backup support.
        
        Args:
            data: Dictionary to write to file
            
        Returns:
            bool: True if write was successful
        """
        async with self._lock:
            for attempt in range(self.max_retries):
                try:
                    # Write to temp file first
                    async with aiofiles.open(self._temp_path, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(data, indent=2, default=str))
                    
                    # Backup current file if it exists
                    if self.file_path.exists():
                        await aiofiles.os.replace(self.file_path, self._backup_path)
                    
                    # Atomic move of temp file to target
                    await aiofiles.os.replace(self._temp_path, self.file_path)
                    
                    logger.debug(f"Successfully wrote to {self.file_path}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Write attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.max_retries - 1:
                        await self._handle_write_failure(e)
                        return False
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
    async def atomic_read(self) -> Optional[Dict[str, Any]]:
        """Read data from file with backup recovery.
        
        Returns:
            Optional[Dict]: File contents or None if read fails
        """
        async with self._lock:
            try:
                async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content)
            except FileNotFoundError:
                logger.warning(f"File {self.file_path} not found")
                return None
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {self.file_path}")
                return await self._recover_from_backup()
            except Exception as e:
                logger.error(f"Read error: {str(e)}")
                return await self._recover_from_backup()
                
    async def _recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """Attempt to recover data from backup file.
        
        Returns:
            Optional[Dict]: Recovered data or None if recovery fails
        """
        if not self._backup_path.exists():
            logger.error("No backup file available for recovery")
            return None
            
        try:
            async with aiofiles.open(self._backup_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
            # Restore backup to main file
            await aiofiles.os.replace(self._backup_path, self.file_path)
            logger.info(f"Recovered data from backup {self._backup_path}")
            return data
            
        except Exception as e:
            logger.error(f"Backup recovery failed: {str(e)}")
            return None
            
    async def _handle_write_failure(self, error: Exception):
        """Handle write operation failure.
        
        Args:
            error: The exception that caused the failure
        """
        logger.error(f"All write attempts failed: {str(error)}")
        
        # Attempt to restore from backup if available
        if self._backup_path.exists():
            try:
                await aiofiles.os.replace(self._backup_path, self.file_path)
                logger.info("Restored from backup after write failure")
            except Exception as e:
                logger.error(f"Failed to restore from backup: {str(e)}")
                
    async def validate_file(self) -> bool:
        """Validate the file's JSON structure.
        
        Returns:
            bool: True if file is valid
        """
        try:
            data = await self.atomic_read()
            if data is None:
                return False
            # Basic structure validation
            return isinstance(data, dict)
        except Exception:
            return False
            
    async def cleanup(self):
        """Clean up temporary files."""
        try:
            if self._temp_path.exists():
                await aiofiles.os.remove(self._temp_path)
        except Exception as e:
            logger.error(f"Failed to cleanup temp file: {str(e)}") 