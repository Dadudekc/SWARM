"""
Agent Loop Module
----------------
Monitors agent inboxes and processes incoming prompts.
"""

import os
import json
import time
import logging
import asyncio
import discord
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .agent_control.controller import AgentController
from .agent_logger import AgentLogger
from .message_processor import MessageProcessor
from .persistent_queue import PersistentQueue
from .dreamscribe import Dreamscribe
from social.utils.log_manager import LogManager
from social.utils.log_config import LogConfig

# Configure logging
logger = logging.getLogger("AgentLoop")
logging.basicConfig(level=logging.DEBUG)

class AgentLoop:
    """Monitors agent inboxes and processes incoming prompts."""
    
    def __init__(self, controller: Any):
        """Initialize the agent loop.
        
        Args:
            controller: The agent controller instance
        """
        self.controller = controller
        self.inbox_path = Path("D:/SWARM/Dream.OS/runtime/agent_memory")
        self.processed_messages = set()
        
        # Initialize Dreamscribe for memory logging
        self.dreamscribe = Dreamscribe()
        
        # Initialize LogManager with custom config
        log_config = LogConfig(
            log_dir=str(Path.cwd() / "logs" / "agent_loop"),
            batch_size=10,
            batch_timeout=1.0,
            max_retries=3,
            retry_delay=0.5
        )
        self.log_manager = LogManager(config=log_config)
        
        # Log initialization
        self.log_manager.info(
            platform="agent_loop",
            status="initialized",
            message="Agent loop initialized with Dreamscribe integration"
        )
        
    def _load_inbox(self, agent_id: str) -> List[dict]:
        """Load messages from an agent's inbox.
        
        Args:
            agent_id: The agent ID to load inbox for
            
        Returns:
            List of messages in the inbox
        """
        try:
            inbox_file = self.inbox_path / agent_id / "inbox.json"
            if not inbox_file.exists():
                return []
                
            with open(inbox_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading inbox for agent {agent_id}: {e}")
            return []
            
    def _process_inbox(self, agent_id: str) -> None:
        """Process messages in an agent's inbox.
        
        Args:
            agent_id: The agent ID to process inbox for
        """
        messages = self._load_inbox(agent_id)
        for msg in messages:
            msg_id = f"{agent_id}:{msg.get('id', '')}"
            if msg_id in self.processed_messages:
                continue
                
            try:
                # Process the message
                content = msg.get('content', '')
                if content:
                    # Log to Dreamscribe before processing
                    memory_fragment = {
                        "timestamp": time.time(),
                        "agent_id": agent_id,
                        "content": content,
                        "context": {
                            "source": "agent_loop",
                            "type": "content_generated",
                            "message_id": msg_id,
                            "task_id": msg.get('task_id', 'unknown')
                        }
                    }
                    self.dreamscribe.ingest_devlog(memory_fragment)
                    
                    self.log_manager.info(
                        platform="agent_loop",
                        status="processing",
                        message=f"Processing message for agent {agent_id}",
                        metadata={
                            "agent_id": agent_id,
                            "message_id": msg_id,
                            "content_preview": content[:50]
                        }
                    )
                    
                    # Process message and get response
                    response = self.controller.message_processor.send_message(
                        agent_id, content, "NORMAL"
                    )
                    
                    # Log response to Dreamscribe
                    if response:
                        response_fragment = {
                            "timestamp": time.time(),
                            "agent_id": agent_id,
                            "content": response,
                            "context": {
                                "source": "agent_loop",
                                "type": "task_completed",
                                "message_id": msg_id,
                                "task_id": msg.get('task_id', 'unknown'),
                                "status": "success"
                            }
                        }
                        self.dreamscribe.ingest_devlog(response_fragment)
                    
                # Mark as processed
                self.processed_messages.add(msg_id)
                
                self.log_manager.info(
                    platform="agent_loop",
                    status="processed",
                    message=f"Successfully processed message for agent {agent_id}",
                    metadata={
                        "agent_id": agent_id,
                        "message_id": msg_id
                    }
                )
                
            except Exception as e:
                # Log error to Dreamscribe
                error_fragment = {
                    "timestamp": time.time(),
                    "agent_id": agent_id,
                    "content": str(e),
                    "context": {
                        "source": "agent_loop",
                        "type": "task_completed",
                        "message_id": msg_id,
                        "task_id": msg.get('task_id', 'unknown'),
                        "status": "error"
                    }
                }
                self.dreamscribe.ingest_devlog(error_fragment)
                
                self.log_manager.error(
                    platform="agent_loop",
                    status="error",
                    message=f"Error processing message for agent {agent_id}",
                    error=str(e),
                    metadata={
                        "agent_id": agent_id,
                        "message_id": msg_id
                    }
                )
                logger.error(f"Error processing message for agent {agent_id}: {e}")
                
    def run(self) -> None:
        """Run the agent loop."""
        self.log_manager.info(
            platform="agent_loop",
            status="started",
            message="Starting agent loop"
        )
        logger.info("Starting agent loop...")
        
        while True:
            try:
                # Process each agent's inbox
                for agent_id in self.controller.coordinate_manager.coordinates.keys():
                    self._process_inbox(agent_id)
                    
                # Sleep to prevent excessive CPU usage
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.log_manager.info(
                    platform="agent_loop",
                    status="stopped",
                    message="Agent loop stopped by user"
                )
                logger.info("Agent loop stopped by user")
                break
            except Exception as e:
                self.log_manager.error(
                    platform="agent_loop",
                    status="error",
                    message="Error in agent loop",
                    error=str(e)
                )
                logger.error(f"Error in agent loop: {e}")
                time.sleep(5)  # Longer sleep on error
            finally:
                # Log metrics before shutdown
                metrics = self.log_manager.get_metrics()
                self.log_manager.info(
                    platform="agent_loop",
                    status="metrics",
                    message="Agent loop metrics at shutdown",
                    metadata=metrics
                )
                
                # Cleanup
                self.log_manager.shutdown()

def start_agent_loops() -> None:
    """Start the agent loops."""
    controller = AgentController()  # Create controller instance
    loop = AgentLoop(controller)
    loop.run()

if __name__ == "__main__":
    start_agent_loops() 