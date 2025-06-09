"""
Message Processor Module
-----------------------
Handles message processing and routing.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from dreamos.core.logging.log_config import LogConfig, LogLevel
from dreamos.core.logging.log_manager import LogManager
from dreamos.core.messaging.message import Message

class MessageProcessor:
    """Processes and routes messages between components."""
    
    def __init__(self, runtime_dir: str):
        """Initialize message processor.
        
        Args:
            runtime_dir: Directory for runtime files
        """
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up message storage
        self.inbox_path = self.runtime_dir / "inbox.json"
        self.outbox_path = self.runtime_dir / "outbox.json"
        
        # Initialize message queues
        self.inbox = asyncio.Queue()
        self.outbox = asyncio.Queue()
        
        # Initialize message handlers
        self.handlers: Dict[str, List[Callable]] = {}
        
        # Set up logging
        log_dir = self.runtime_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_config = LogConfig(
            level=LogLevel.INFO,
            log_dir=str(log_dir),
            file_path=str(log_dir / "message_processor.log"),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = LogManager(config=log_config)
        
        # Load existing messages
        self._load_messages()
        
    def _load_messages(self):
        """Load existing messages from storage."""
        try:
            if self.inbox_path.exists():
                with open(self.inbox_path) as f:
                    messages = json.load(f)
                    for msg in messages:
                        self.inbox.put_nowait(Message.from_dict(msg))
                        
            if self.outbox_path.exists():
                with open(self.outbox_path) as f:
                    messages = json.load(f)
                    for msg in messages:
                        self.outbox.put_nowait(Message.from_dict(msg))
        except Exception as e:
            self.logger.error(f"Error loading messages: {e}")
            
    def _save_messages(self):
        """Save messages to storage."""
        try:
            # Save inbox
            inbox_messages = []
            while not self.inbox.empty():
                msg = self.inbox.get_nowait()
                inbox_messages.append(msg.to_dict())
                self.inbox.put_nowait(msg)
                
            with open(self.inbox_path, 'w') as f:
                json.dump(inbox_messages, f, indent=2)
                
            # Save outbox
            outbox_messages = []
            while not self.outbox.empty():
                msg = self.outbox.get_nowait()
                outbox_messages.append(msg.to_dict())
                self.outbox.put_nowait(msg)
                
            with open(self.outbox_path, 'w') as f:
                json.dump(outbox_messages, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving messages: {e}")
            
    async def start(self):
        """Start message processing."""
        self.logger.info("Starting message processor")
        asyncio.create_task(self._process_messages())
        
    async def stop(self):
        """Stop message processing."""
        self.logger.info("Stopping message processor")
        self._save_messages()
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        
    def unregister_handler(self, message_type: str, handler: Callable):
        """Unregister a message handler.
        
        Args:
            message_type: Type of message
            handler: Handler function to remove
        """
        if message_type in self.handlers:
            self.handlers[message_type].remove(handler)
            
    async def send_message(self, message: Message):
        """Send a message.
        
        Args:
            message: Message to send
        """
        await self.outbox.put(message)
        self.logger.info(f"Queued message: {message}")
        
    async def _process_messages(self):
        """Process messages from queues."""
        while True:
            try:
                # Process outbox
                if not self.outbox.empty():
                    message = await self.outbox.get()
                    if message.type in self.handlers:
                        for handler in self.handlers[message.type]:
                            try:
                                await handler(message)
                            except Exception as e:
                                self.logger.error(f"Error in message handler: {e}")
                    self.outbox.task_done()
                    
                # Process inbox
                if not self.inbox.empty():
                    message = await self.inbox.get()
                    if message.type in self.handlers:
                        for handler in self.handlers[message.type]:
                            try:
                                await handler(message)
                            except Exception as e:
                                self.logger.error(f"Error in message handler: {e}")
                    self.inbox.task_done()
                    
                # Save messages periodically
                self._save_messages()
                
                # Sleep briefly to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(1)  # Back off on error 
