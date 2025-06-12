"""
Message validator implementation for Dream.OS agent communication.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from .base import Message, MessageValidator, MessageType, MessagePriority

logger = logging.getLogger("dreamos.messaging")

class MessageValidator(MessageValidator):
    """Validator for ensuring message integrity."""
    
    def __init__(self):
        """Initialize validator."""
        # Message size limits
        self.max_content_size = 1024 * 1024  # 1MB
        self.max_metadata_size = 1024  # 1KB
        
        # Rate limiting
        self.rate_limits: Dict[str, Tuple[int, timedelta]] = {}  # agent_id -> (max_messages, time_window)
        self.message_counts: Dict[str, List[datetime]] = {}  # agent_id -> list of message timestamps
        
        # Content validation
        self.content_patterns: Dict[MessageType, re.Pattern] = {}  # message type -> content pattern
        self.required_fields: Dict[MessageType, Set[str]] = {}  # message type -> set of required fields
    
    def set_rate_limit(self, agent_id: str, max_messages: int, time_window: timedelta) -> None:
        """Set rate limit for an agent.
        
        Args:
            agent_id: ID of agent to set limit for
            max_messages: Maximum number of messages allowed in time window
            time_window: Time window for rate limiting
        """
        self.rate_limits[agent_id] = (max_messages, time_window)
        logger.debug(f"Set rate limit for {agent_id}: {max_messages} messages per {time_window}")
    
    def set_content_pattern(self, message_type: MessageType, pattern: str) -> None:
        """Set content validation pattern for a message type.
        
        Args:
            message_type: Type of message to set pattern for
            pattern: Regex pattern for content validation
        """
        self.content_patterns[message_type] = re.compile(pattern)
        logger.debug(f"Set content pattern for {message_type}: {pattern}")
    
    def set_required_fields(self, message_type: MessageType, fields: Set[str]) -> None:
        """Set required fields for a message type.
        
        Args:
            message_type: Type of message to set fields for
            fields: Set of required field names
        """
        self.required_fields[message_type] = fields
        logger.debug(f"Set required fields for {message_type}: {fields}")
    
    async def validate(self, message: Message) -> Tuple[bool, Optional[str]]:
        """Validate a message.
        
        Args:
            message: Message to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Check basic message structure
            if not message.id or not message.type or not message.sender or not message.recipient:
                return False, "Missing required message fields"
            
            # Check message size
            if len(str(message.content)) > self.max_content_size:
                return False, f"Message content exceeds size limit of {self.max_content_size} bytes"
            
            if len(str(message.metadata)) > self.max_metadata_size:
                return False, f"Message metadata exceeds size limit of {self.max_metadata_size} bytes"
            
            # Check rate limits
            if message.sender in self.rate_limits:
                max_messages, time_window = self.rate_limits[message.sender]
                now = datetime.now()
                
                # Initialize message counts if needed
                if message.sender not in self.message_counts:
                    self.message_counts[message.sender] = []
                
                # Remove old timestamps
                cutoff = now - time_window
                self.message_counts[message.sender] = [
                    ts for ts in self.message_counts[message.sender]
                    if ts > cutoff
                ]
                
                # Check if limit exceeded
                if len(self.message_counts[message.sender]) >= max_messages:
                    return False, f"Rate limit exceeded: {max_messages} messages per {time_window}"
                
                # Add new timestamp
                self.message_counts[message.sender].append(now)
            
            # Check content pattern
            if message.type in self.content_patterns:
                pattern = self.content_patterns[message.type]
                if not pattern.match(str(message.content)):
                    return False, f"Message content does not match required pattern for {message.type}"
            
            # Check required fields
            if message.type in self.required_fields:
                required = self.required_fields[message.type]
                missing = required - set(message.metadata.keys())
                if missing:
                    return False, f"Missing required fields for {message.type}: {missing}"
            
            logger.debug(f"Message {message.id} validated successfully")
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating message {message.id}: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def validate_batch(self, messages: List[Message]) -> List[Tuple[Message, bool, Optional[str]]]:
        """Validate a batch of messages.
        
        Args:
            messages: List of messages to validate
            
        Returns:
            List[Tuple[Message, bool, Optional[str]]]: List of (message, is_valid, error_message)
        """
        results = []
        for message in messages:
            is_valid, error = await self.validate(message)
            results.append((message, is_valid, error))
        return results 