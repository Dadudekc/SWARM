"""
Log Batcher
---------
Batches and processes logs.
"""

import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from ...core.utils.core_utils import atomic_write
from .log_manager import LogManager

logger = logging.getLogger(__name__)

class LogBatcher:
    """Handles batched logging operations for efficiency."""
    
    def __init__(
        self,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
        log_dir: Optional[str] = None
    ):
        """Initialize log batcher.
        
        Args:
            batch_size: Maximum number of logs per batch
            batch_timeout: Maximum time to wait before flushing batch
            log_dir: Directory to store log files
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._batch: List[Dict[str, Any]] = []
        self._last_flush = time.time()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the log batcher."""
        if self._running:
            return
            
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("Log batcher started")
        
    async def stop(self) -> None:
        """Stop the log batcher."""
        if not self._running:
            return
            
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
                
        await self.flush()
        logger.info("Log batcher stopped")
        
    async def add_log(self, log_entry: Dict[str, Any]) -> None:
        """Add a log entry to the current batch.
        
        Args:
            log_entry: Log entry to add
        """
        log_entry['timestamp'] = datetime.utcnow().isoformat()
        self._batch.append(log_entry)
        
        if len(self._batch) >= self.batch_size:
            await self.flush()
            
    async def flush(self) -> None:
        """Flush the current batch to disk."""
        if not self._batch:
            return
            
        try:
            # Create log file path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"batch_{timestamp}.log"
            
            # Write batch to file
            content = "\n".join(str(entry) for entry in self._batch)
            atomic_write(log_file, content)
            
            # Clear batch
            self._batch = []
            self._last_flush = time.time()
            
            logger.debug(f"Flushed {len(self._batch)} logs to {log_file}")
            
        except Exception as e:
            logger.error(f"Error flushing log batch: {e}")
            
    async def _flush_loop(self) -> None:
        """Periodically flush logs based on timeout."""
        while self._running:
            try:
                await asyncio.sleep(1)
                
                if time.time() - self._last_flush >= self.batch_timeout:
                    await self.flush()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
                
    def get_batch_size(self) -> int:
        """Get current batch size.
        
        Returns:
            Number of logs in current batch
        """
        return len(self._batch)
        
    def is_running(self) -> bool:
        """Check if batcher is running.
        
        Returns:
            True if running
        """
        return self._running 
