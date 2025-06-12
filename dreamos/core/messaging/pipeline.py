"""
Message processing pipeline for Dream.OS.

This module provides a unified pipeline for processing messages, including:
- Message validation
- Message routing
- Message processing
- Response handling
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Generic
from pathlib import Path

from .unified_message_system import Message, MessageQueue, MessageProcessor
from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error

T = TypeVar('T')

class MessagePipeline(Generic[T]):
    """Handles the processing of messages through the system."""
    
    def __init__(
        self,
        queue: MessageQueue[T],
        batch_size: int = 10,
        batch_timeout: float = 1.0
    ):
        """Initialize the message pipeline.
        
        Args:
            queue: Message queue to process
            batch_size: Maximum number of messages to process in a batch
            batch_timeout: Maximum time to wait for batch completion
        """
        self.queue = queue
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._processing = False
        self._batch_lock = asyncio.Lock()
        self._current_batch: List[Message[T]] = []
        self._metrics = {
            'batch': metrics.counter(
                'message_pipeline_batch_total',
                'Total message batches processed',
                ['result']
            ),
            'error': metrics.counter(
                'message_pipeline_error_total',
                'Total pipeline errors',
                ['operation']
            ),
            'duration': metrics.histogram(
                'message_pipeline_duration_seconds',
                'Pipeline operation duration',
                ['operation']
            )
        }
    
    @log_operation('pipeline_process', metrics='batch', duration='duration')
    async def process_message(self, message: Message[T]) -> bool:
        """Process a single message.
        
        Args:
            message: Message to process
            
        Returns:
            True if processing was successful
        """
        try:
            # Add to current batch
            async with self._batch_lock:
                self._current_batch.append(message)
                
                # Process batch if full
                if len(self._current_batch) >= self.batch_size:
                    return await self._process_batch()
                
                return True
                
        except Exception as e:
            error = handle_error(e, {
                "message": message.message_id,
                "operation": "process_message"
            })
            logger.error(f"Error processing message: {str(error)}")
            self._metrics['error'].labels(
                operation="process_message"
            ).inc()
            return False
    
    async def _process_batch(self) -> bool:
        """Process current batch of messages.
        
        Returns:
            True if batch processing was successful
        """
        try:
            # Get current batch
            async with self._batch_lock:
                batch = self._current_batch
                self._current_batch = []
            
            if not batch:
                return True
            
            # Process messages in parallel
            tasks = []
            for message in batch:
                task = asyncio.create_task(self._process_single(message))
                tasks.append(task)
            
            # Wait for completion with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks),
                    timeout=self.batch_timeout
                )
                success = True
            except asyncio.TimeoutError:
                logger.warning("Batch processing timed out")
                success = False
            
            # Record metrics
            self._metrics['batch'].labels(
                result="success" if success else "timeout"
            ).inc()
            
            return success
            
        except Exception as e:
            error = handle_error(e, {
                "operation": "process_batch",
                "batch_size": len(batch)
            })
            logger.error(f"Error processing batch: {str(error)}")
            self._metrics['error'].labels(
                operation="process_batch"
            ).inc()
            return False
    
    async def _process_single(self, message: Message[T]) -> bool:
        """Process a single message.
        
        Args:
            message: Message to process
            
        Returns:
            True if processing was successful
        """
        try:
            # Enqueue message
            success = await self.queue.enqueue(message)
            if not success:
                logger.error(f"Failed to enqueue message: {message.message_id}")
                return False
            
            return True
            
        except Exception as e:
            error = handle_error(e, {
                "message": message.message_id,
                "operation": "process_single"
            })
            logger.error(f"Error processing message: {str(error)}")
            self._metrics['error'].labels(
                operation="process_single"
            ).inc()
            return False
    
    async def start(self):
        """Start the message pipeline."""
        if self._processing:
            logger.warning("Pipeline already running")
            return
        
        self._processing = True
        logger.info("Message pipeline started")
    
    async def stop(self):
        """Stop the message pipeline."""
        if not self._processing:
            logger.warning("Pipeline not running")
            return
        
        self._processing = False
        
        # Process any remaining messages
        if self._current_batch:
            await self._process_batch()
        
        logger.info("Message pipeline stopped") 
