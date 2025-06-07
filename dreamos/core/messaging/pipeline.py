"""
Message processing pipeline for handling message flow through the system.

This module provides a unified pipeline for processing messages, including:
- Message validation
- Message routing
- Message processing
- Response handling
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .message import Message
from .enums import MessageMode, MessageStatus
from ..agent_control.ui_automation import UIAutomation
from ..shared.persistent_queue import PersistentQueue

logger = logging.getLogger(__name__)

class MessagePipeline:
    """Handles the processing of messages through the system."""
    
    def __init__(
        self,
        ui_automation: UIAutomation,
        queue: Optional[PersistentQueue] = None,
        batch_size: int = 10,
        batch_timeout: float = 1.0
    ):
        """Initialize the message pipeline.
        
        Args:
            ui_automation: The UI automation instance for agent interaction
            queue: Optional persistent queue for message storage
            batch_size: Maximum number of messages to process in a batch
            batch_timeout: Maximum time to wait for batch completion
        """
        self.ui_automation = ui_automation
        self.queue = queue or PersistentQueue()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._processing = False
        self._batch_lock = asyncio.Lock()
        self._current_batch: List[Message] = []
        
    async def process_message(self, message: Message) -> bool:
        """Process a single message.
        
        Args:
            message: The message to process
            
        Returns:
            bool: True if processing was successful
        """
        try:
            # Validate message
            if not self._validate_message(message):
                logger.error(f"Invalid message: {message}")
                return False
                
            # Add to queue
            self.queue.enqueue(message)
            
            # Process message
            success = await self._process_single(message)
            if not success:
                logger.error(f"Failed to process message: {message}")
                return False
                
            return True
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return False
            
    async def process_batch(self, messages: List[Message]) -> bool:
        """Process a batch of messages.
        
        Args:
            messages: List of messages to process
            
        Returns:
            bool: True if all messages were processed successfully
        """
        async with self._batch_lock:
            try:
                # Validate messages
                if not all(self._validate_message(msg) for msg in messages):
                    logger.error("Invalid messages in batch")
                    return False
                    
                # Add to queue
                for message in messages:
                    self.queue.enqueue(message)
                    
                # Process batch
                success = await self._process_batch(messages)
                if not success:
                    logger.error("Failed to process message batch")
                    return False
                    
                return True
                
            except Exception as e:
                logger.exception(f"Error processing message batch: {e}")
                return False
                
    def _validate_message(self, message: Message) -> bool:
        """Validate a message.
        
        Args:
            message: The message to validate
            
        Returns:
            bool: True if message is valid
        """
        if not message.content:
            logger.error("Message has no content")
            return False
            
        if not message.sender:
            logger.error("Message has no sender")
            return False
            
        if not message.timestamp:
            logger.error("Message has no timestamp")
            return False
            
        return True
        
    async def _process_single(self, message: Message) -> bool:
        """Process a single message.
        
        Args:
            message: The message to process
            
        Returns:
            bool: True if processing was successful
        """
        try:
            # Move to agent
            if not self.ui_automation.move_to_agent(message.to_agent):
                logger.error(f"Failed to move to agent: {message.to_agent}")
                return False
                
            # Click input box
            if not self.ui_automation.click_input_box(message.to_agent):
                logger.error(f"Failed to click input box for agent: {message.to_agent}")
                return False
                
            # Send message
            if not self.ui_automation.send_message(message.to_agent, message.content):
                logger.error(f"Failed to send message to agent: {message.to_agent}")
                return False
                
            # Click copy button
            if not self.ui_automation.click_copy_button(message.to_agent):
                logger.error(f"Failed to click copy button for agent: {message.to_agent}")
                return False
                
            return True
            
        except Exception as e:
            logger.exception(f"Error in message processing: {e}")
            return False
            
    async def _process_batch(self, messages: List[Message]) -> bool:
        """Process a batch of messages.
        
        Args:
            messages: List of messages to process
            
        Returns:
            bool: True if all messages were processed successfully
        """
        try:
            # Group messages by agent
            agent_messages: Dict[str, List[Message]] = {}
            for message in messages:
                if message.to_agent not in agent_messages:
                    agent_messages[message.to_agent] = []
                agent_messages[message.to_agent].append(message)
                
            # Process each agent's messages
            for agent_id, agent_msgs in agent_messages.items():
                # Move to agent
                if not self.ui_automation.move_to_agent(agent_id):
                    logger.error(f"Failed to move to agent: {agent_id}")
                    return False
                    
                # Click input box
                if not self.ui_automation.click_input_box(agent_id):
                    logger.error(f"Failed to click input box for agent: {agent_id}")
                    return False
                    
                # Send messages
                for message in agent_msgs:
                    if not self.ui_automation.send_message(agent_id, message.content):
                        logger.error(f"Failed to send message to agent: {agent_id}")
                        return False
                        
                # Click copy button
                if not self.ui_automation.click_copy_button(agent_id):
                    logger.error(f"Failed to click copy button for agent: {agent_id}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.exception(f"Error in batch processing: {e}")
            return False 