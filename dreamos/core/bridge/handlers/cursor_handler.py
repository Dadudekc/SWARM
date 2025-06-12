"""
Cursor Bridge Handler
------------------
Handles communication between agents and the Cursor IDE.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from dreamos.bridge_clients.cursor import CursorBridge
from dreamos.core.bridge.base import BridgeHandler
from dreamos.core.bridge.monitoring import BridgeMonitor
from dreamos.core.bridge.validation import BridgeValidator
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.json_utils import load_json, save_json
from ...utils.metrics import metrics, logger, log_operation
from ...utils.exceptions import handle_error

logger = logging.getLogger(__name__)

class CursorBridgeHandler(BridgeHandler):
    """Cursor bridge handler with unified logging and metrics."""
    
    def __init__(
        self,
        watch_dir: Path,
        file_pattern: str = "*.json",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the Cursor bridge handler.
        
        Args:
            watch_dir: Directory to watch for messages
            file_pattern: Pattern to match message files
            config: Optional configuration dictionary
        """
        super().__init__(watch_dir, file_pattern, config)
        self.logger = logging.getLogger(__name__)
        self.bridge = CursorBridge()
        self.validator = BridgeValidator(config)
        self.monitor = BridgeMonitor(config)
        self.processed_items: set[str] = set()
        self._metrics = {
            'processed': metrics.counter('cursor_processed_total', 'Total files processed'),
            'errors': metrics.counter('cursor_errors_total', 'Total errors', ['error_type']),
            'duration': metrics.histogram('cursor_operation_duration_seconds', 'Operation duration', ['operation'])
        }
        
    async def start(self):
        """Start the bridge handler.
        
        This method:
        1. Starts the bridge monitor
        2. Initializes the bridge
        3. Starts the bridge
        """
        self.logger.info("Starting Cursor bridge handler")
        self.monitor.start()
        await self.bridge.start()
        self.logger.info("Cursor bridge handler started")
        
    async def stop(self):
        """Stop the bridge handler.
        
        This method:
        1. Stops the bridge
        2. Stops the bridge monitor
        3. Cleans up any resources
        """
        self.logger.info("Stopping Cursor bridge handler")
        await self.bridge.stop()
        self.monitor.stop()
        self.logger.info("Cursor bridge handler stopped")
        
    @log_operation('cursor_process', metrics='processed', duration='duration')
    async def process_file(self, file_path: Path) -> bool:
        """Process a file.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            bool: True if processing was successful
        """
        try:
            if file_path.name in self.processed_items:
                logger.debug(f"Skipping already processed file: {file_path}")
                return True
                
            if self.process_callback:
                await self.process_callback(file_path)
                
            self.processed_items.add(file_path.name)
            logger.info(
                "file_processed",
                extra={
                    "path": str(file_path),
                    "name": file_path.name
                }
            )
            return True
            
        except Exception as e:
            error = handle_error(e, {"path": str(file_path), "operation": "process"})
            await self.handle_error(error, file_path)
            return False
    
    @log_operation('cursor_error', metrics='errors')
    async def handle_error(self, error: Exception, file_path: Path) -> None:
        """Handle an error.
        
        Args:
            error: Error that occurred
            file_path: Path to file that caused error
        """
        logger.error(
            "file_processing_error",
            extra={
                "path": str(file_path),
                "error": str(error),
                "error_type": error.__class__.__name__
            }
        )
        self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
        
        if self.error_callback:
            await self.error_callback(error, file_path)
    
    @log_operation('cursor_cleanup')
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.stop()
            self.processed_items.clear()
            logger.info("cursor_cleanup_complete")
        except Exception as e:
            error = handle_error(e, {"operation": "cleanup"})
            logger.error(
                "cursor_cleanup_error",
                extra={
                    "error": str(error),
                    "error_type": error.__class__.__name__
                }
            )
            self._metrics['errors'].labels(error_type=error.__class__.__name__).inc()
            raise 