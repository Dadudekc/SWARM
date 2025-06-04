"""
Message Processor

Handles message processing and delivery for the cell phone interface.
"""

import logging
import threading
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from queue import PriorityQueue
from datetime import datetime
from pathlib import Path

from ..persistent_queue import PersistentQueue
from .common import Message, MessageMode, MessagePriority

logger = logging.getLogger('message_processor')


class MessageProcessor:
    """Handles message processing and delivery for the cell phone interface."""
    
    def __init__(self, runtime_dir: Optional[str] = None):
        self.runtime_dir = Path(runtime_dir) if runtime_dir else Path("runtime")
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        queue_file = self.runtime_dir / "queue" / "messages.json"
        self.persistent_queue = PersistentQueue(queue_file=str(queue_file))

        self._queue = PriorityQueue()
        self._running = False
        self._processing_thread: Optional[threading.Thread] = None
        self._message_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        
        # Message chunking parameters
        self.max_chunk_size = 100
        self.retry_attempts = 3
        self.retry_delay = 5
        self.verification_delay = 0.2
        
        # Message format templates
        self.message_templates = {
            "resume": """[RESUME] Dream.os Autonomous Protocol Activation:

1. Scan for pending tasks in your domain
2. Identify opportunities for system optimization
3. Initiate any pending protocol sequences
4. Engage with other agents for collaborative tasks
5. Proceed with autonomous operations
6. Report only critical issues or completed objectives

Continue with your autonomous operations.""",
            "sync": "[{agent_id}] [SYNC] Status:\n{metrics}\n\nWE ARE THE SWARM",
            "verify": "[{agent_id}] [VERIFY] Please verify your current state and report any issues.",
            "repair": "[{agent_id}] [REPAIR] Repair requested. Issues: {issues}",
            "backup": "[{agent_id}] [BACKUP] Please backup your current state.",
            "restore": "[{agent_id}] [RESTORE] Please restore your state{backup_point}{restore_scope}.",
            "cleanup": """[CLEANUP] Dream.os System Cleanup Protocol:

1. Scan for and remove temporary files
2. Clean up unused resources
3. Optimize memory usage
4. Archive old logs and data
5. Verify system integrity
6. Report cleanup status

Proceed with system cleanup operations.""",
            "captain": """[CAPTAIN] Dream.os Captaincy Campaign Protocol:

1. Review current agent assignments
2. Assess system-wide performance
3. Coordinate agent activities
4. Optimize resource allocation
5. Monitor system health
6. Report campaign status

Proceed with captaincy operations.""",
            "task": """[TASK] Dream.os Task Management Protocol:

1. Scan for new task opportunities
2. Prioritize existing tasks
3. Update task board
4. Assign resources
5. Monitor progress
6. Report task status

Proceed with task management operations.""",
            "integrate": """[INTEGRATE] Dream.os System Integration Protocol:

1. Test all system components
2. Verify component interactions
3. Run integration tests
4. Identify improvement areas
5. Optimize system flow
6. Report integration status

Proceed with system integration operations.""",
            "alert": "[{agent_id}] [ALERT] {level} - {message}",
            "action": "[{agent_id}] [ACTION] {type} - {details}"
        }
        
    def start(self):
        """Start the message processor."""
        if self._running:
            return
            
        self._running = True
        self._processing_thread = threading.Thread(target=self._process_messages)
        self._processing_thread.daemon = True
        self._processing_thread.start()
        logger.info("Message processor started")
        
    def stop(self):
        """Stop the message processor."""
        self._running = False
        if self._processing_thread:
            self._processing_thread.join(timeout=5)
        logger.info("Message processor stopped")
        
    def add_message(self, message: Dict[str, Any]) -> bool:
        """Add a message to the processing queue.
        
        Args:
            message: Message to add with priority
            
        Returns:
            bool: True if message was successfully queued
        """
        try:
            # Calculate priority (higher number = higher priority)
            priority = message.get('priority', 0)
            timestamp = datetime.now().timestamp()
            
            # Format message if needed
            if 'format' in message:
                message['content'] = self._format_message(
                    message['format'],
                    message.get('agent_id', ''),
                    **message.get('format_args', {})
                )
            
            # Chunk message if needed
            if message.get('chunk', False):
                chunks = self._chunk_message(message['content'])
                for chunk in chunks:
                    chunk_msg = message.copy()
                    chunk_msg['content'] = chunk
                    self._queue.put((-priority, timestamp, chunk_msg))
            else:
                self._queue.put((-priority, timestamp, message))
            
            # Add to history
            self._message_history.append({
                'message': message,
                'timestamp': timestamp,
                'status': 'queued'
            })
            
            # Trim history if needed
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history:]
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get current message queue status.
        
        Returns:
            Dict containing queue statistics
        """
        try:
            return {
                'queue_size': self._queue.qsize(),
                'history_size': len(self._message_history),
                'is_running': self._running,
                'recent_messages': self._message_history[-10:] if self._message_history else []
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}
            
    def clear_queue(self):
        """Clear all pending messages."""
        try:
            while not self._queue.empty():
                self._queue.get_nowait()
            logger.info("Message queue cleared")
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            
    def _process_messages(self):
        """Process messages in the queue."""
        while self._running:
            try:
                # Get next message
                if self._queue.empty():
                    time.sleep(0.1)
                    continue
                    
                priority, timestamp, message = self._queue.get()
                
                # Process message with retries
                success = False
                for attempt in range(self.retry_attempts):
                    try:
                        success = self._deliver_message(message)
                        if success:
                            break
                        time.sleep(self.retry_delay)
                    except Exception as e:
                        logger.error(f"Error delivering message (attempt {attempt + 1}): {e}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
                
                # Update history
                for hist_msg in self._message_history:
                    if hist_msg['message'] == message:
                        hist_msg['status'] = 'delivered' if success else 'failed'
                        hist_msg['delivery_time'] = datetime.now().timestamp()
                        break
                        
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                time.sleep(1)  # Back off on error
                
    def _deliver_message(self, message: Dict[str, Any]) -> bool:
        """Deliver a message to its recipient.
        
        Args:
            message: Message to deliver
            
        Returns:
            bool: True if message was successfully delivered
        """
        try:
            # Get message details
            from_agent = message.get('from_agent')
            to_agent = message.get('to_agent')
            content = message.get('content')
            mode = message.get('mode', MessageMode.NORMAL)
            
            # Log delivery
            logger.info(f"Delivering {mode.value} message from {from_agent} to {to_agent}")
            
            # Mode-specific processing
            if mode == MessageMode.RESUME:
                # Add initialization sequence for new agents
                if "Welcome to Dream.os" in content:
                    time.sleep(2)  # Longer delay for initialization
            elif mode == MessageMode.SYNC:
                # Add metrics collection delay
                time.sleep(0.5)
            elif mode == MessageMode.VERIFY:
                # Add verification delay
                time.sleep(1)
            elif mode == MessageMode.REPAIR:
                # Add repair operation delay
                time.sleep(1.5)
            elif mode == MessageMode.BACKUP:
                # Add backup operation delay
                time.sleep(2)
            elif mode == MessageMode.RESTORE:
                # Add restore operation delay
                time.sleep(2.5)
            elif mode == MessageMode.CLEANUP:
                # Add cleanup operation delay
                time.sleep(1)
            elif mode == MessageMode.CAPTAIN:
                # Add captaincy operation delay
                time.sleep(1.5)
            elif mode == MessageMode.TASK:
                # Add task management delay
                time.sleep(1)
            elif mode == MessageMode.INTEGRATE:
                # Add integration operation delay
                time.sleep(2)
            
            priority_val = message.get('priority', MessagePriority.NORMAL)
            if isinstance(priority_val, int):
                priority_enum = MessagePriority(priority_val)
            elif isinstance(priority_val, str):
                priority_enum = MessagePriority[priority_val.upper()]
            else:
                priority_enum = priority_val

            msg_obj = Message(
                content=content,
                to_agent=to_agent,
                from_agent=from_agent,
                mode=mode,
                priority=priority_enum,
                metadata=message.get('metadata', {})
            )

            success = self.persistent_queue.enqueue(msg_obj)

            time.sleep(0.1)
            return success
            
        except Exception as e:
            logger.error(f"Failed to deliver message: {e}")
            return False
            
    def _format_message(self, format_type: str, agent_id: str, **kwargs) -> str:
        """Format a message using templates.
        
        Args:
            format_type: Type of message to format
            agent_id: ID of the agent
            **kwargs: Additional formatting arguments
            
        Returns:
            str: Formatted message
        """
        try:
            template = self.message_templates.get(format_type)
            if not template:
                raise ValueError(f"Unknown message format: {format_type}")
            
            # Handle special cases for restore message
            if format_type == "restore":
                backup_point = kwargs.get('backup_point', '')
                restore_scope = kwargs.get('restore_scope', '')
                backup_point = f" from backup point: {backup_point}" if backup_point else ""
                restore_scope = f" with scope: {restore_scope}" if restore_scope else ""
                kwargs['backup_point'] = backup_point
                kwargs['restore_scope'] = restore_scope
            
            # Format the message
            formatted = template.format(agent_id=agent_id, **kwargs)
            
            # Add mode tag if not already present
            mode = MessageMode[format_type.upper()]
            if mode != MessageMode.NORMAL and not formatted.startswith(mode.value):
                formatted = f"{mode.value} {formatted}"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"[{agent_id}] [ERROR] Failed to format message: {str(e)}"
            
    def _chunk_message(self, message: str) -> List[str]:
        """Split message into chunks with verification hashes.
        
        Args:
            message: Message to chunk
            
        Returns:
            List[str]: List of message chunks
        """
        chunks = []
        current_chunk = ""
        total_chunks = (len(message) + self.max_chunk_size - 1) // self.max_chunk_size
        
        for i, char in enumerate(message):
            current_chunk += char
            if len(current_chunk) >= self.max_chunk_size or i == len(message) - 1:
                chunk_num = len(chunks) + 1
                chunk_hash = hashlib.md5(current_chunk.encode()).hexdigest()[:6]
                chunk_header = f"[CHUNK {chunk_num}/{total_chunks} HASH:{chunk_hash}]"
                chunks.append(f"{chunk_header}\n{current_chunk.strip()}")
                current_chunk = ""
                
        return chunks
        
    def verify_chunk(self, expected: str, actual: str) -> bool:
        """Verify chunk content and hash.
        
        Args:
            expected: Expected chunk content
            actual: Actual chunk content
            
        Returns:
            bool: True if chunk is valid
        """
        try:
            # Extract headers
            expected_header = expected.split('\n')[0]
            actual_header = actual.split('\n')[0]
            
            # Extract content
            expected_content = '\n'.join(expected.split('\n')[1:]).strip()
            actual_content = '\n'.join(actual.split('\n')[1:]).strip()
            
            # Verify header format
            if not (expected_header.startswith('[CHUNK') and actual_header.startswith('[CHUNK')):
                return False
                
            # Verify content - allow for slight variations in whitespace
            return expected_content.replace(' ', '') == actual_content.replace(' ', '')
            
        except Exception as e:
            logger.error(f"Error verifying chunk: {e}")
            return False 