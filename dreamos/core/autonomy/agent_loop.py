"""
Agent Loop Module
----------------
Monitors agent inboxes and processes incoming prompts.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from dreamos.core.utils.core_utils import (
    atomic_write,
    safe_read,
    safe_write,
    get_timestamp,
    format_duration,
    is_valid_uuid
)
from dreamos.core.utils import load_json
from dreamos.core.logging.log_manager import LogManager, LogConfig
from dreamos.core.logging.log_config import LogLevel
from dreamos.core.agent_control.controller import AgentController
from dreamos.core.logging.agent_logger import AgentLogger
from dreamos.core.messaging.message_processor import MessageProcessor
from dreamos.core.shared.persistent_queue import PersistentQueue
from dreamos.core.ai.dreamscribe import Dreamscribe
from dreamos.core.config.config_manager import ConfigManager
from dreamos.utils.discord_client import Client, Command

# Initialize logging
log_config = LogConfig(
    level=LogLevel.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_path="logs/system.log"
)
log_manager = LogManager(config=log_config)
logger = log_manager

class AgentLoop:
    """Monitors agent inboxes and processes incoming prompts."""
    
    def __init__(self, controller: Any):
        """Initialize the agent loop.
        
        Args:
            controller: The agent controller instance
        """
        self.controller = controller
        self.inbox_path = Path("D:/SWARM/Dream.OS/runtime/agent_memory")
        ensure_dir(self.inbox_path)
        self.processed_messages = set()
        self.initialized_agents = set()
        
        # Initialize Dreamscribe for memory logging
        self.dreamscribe = Dreamscribe()
        
        # Initialize LogManager with custom config
        agent_log_config = LogConfig(
            level=LogLevel.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            file_path="logs/agent.log"
        )
        self.log_manager = LogManager(config=agent_log_config)
        
        # Log initialization
        self.log_manager.info(
            message="Agent loop initialized with Dreamscribe integration",
            extra={
                "platform": "agent_loop",
                "status": "initialized"
            }
        )
    
    async def initialize_agent(self, agent_id: str) -> None:
        """Initialize an agent asynchronously.
        
        Args:
            agent_id: The ID of the agent to initialize
        """
        if agent_id in self.initialized_agents:
            return
            
        try:
            agent = self.controller.get_agent(agent_id)
            if hasattr(agent, 'initialize'):
                await agent.initialize()
                self.initialized_agents.add(agent_id)
                self.log_manager.info(
                    message=f"Successfully initialized agent {agent_id}",
                    extra={
                        "platform": "agent_loop",
                        "status": "success",
                        "tags": ["init", "success"]
                    }
                )
        except Exception as e:
            self.log_manager.error(
                message=f"Failed to initialize agent {agent_id}: {str(e)}",
                extra={
                    "platform": "agent_loop",
                    "status": "error",
                    "tags": ["init", "error"]
                }
            )
            raise
    
    async def initialize_all_agents(self) -> None:
        """Initialize all agents in the controller."""
        for agent_id in self.controller.coordinate_manager.coordinates.keys():
            await self.initialize_agent(agent_id)
    
    async def run(self) -> None:
        """Run the agent loop."""
        self.log_manager.info(
            message="Starting agent loop",
            extra={
                "platform": "agent_loop",
                "status": "started"
            }
        )
        logger.info("Starting agent loop...")
        
        # Initialize all agents first
        await self.initialize_all_agents()
        
        while True:
            try:
                # Process each agent's inbox
                for agent_id in self.controller.coordinate_manager.coordinates.keys():
                    # Ensure agent is initialized
                    if agent_id not in self.initialized_agents:
                        await self.initialize_agent(agent_id)
                    await self._process_inbox(agent_id)
                    
                # Sleep to prevent excessive CPU usage
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                self.log_manager.info(
                    message="Agent loop stopped by user",
                    extra={
                        "platform": "agent_loop",
                        "status": "stopped"
                    }
                )
                logger.info("Agent loop stopped by user")
                break
            except Exception as e:
                self.log_manager.error(
                    message="Error in agent loop",
                    extra={
                        "platform": "agent_loop",
                        "status": "error",
                        "error": str(e)
                    }
                )
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(5)  # Longer sleep on error
            finally:
                # Log metrics before shutdown
                metrics = self.log_manager.get_metrics()
                self.log_manager.info(
                    message="Agent loop metrics at shutdown",
                    extra={
                        "platform": "agent_loop",
                        "status": "metrics",
                        "metadata": metrics
                    }
                )
                
                # Cleanup
                self.log_manager.shutdown()

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
                
            return load_json(str(inbox_file))
                
        except Exception as e:
            logger.error(f"Error loading inbox for agent {agent_id}: {e}")
            return []
            
    async def _process_inbox(self, agent_id: str) -> None:
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
                    message = {
                        "type": "agent_message",
                        "agent_id": agent_id,
                        "content": content,
                        "priority": msg.get("priority", "NORMAL"),
                        "task_id": msg.get("task_id", "unknown"),
                        "id": msg.get("id", ""),
                        "timestamp": time.time()
                    }
                    await self.controller.message_processor.send_message(message)
                    
                    # Add to processed messages
                    self.processed_messages.add(msg_id)
                    
                    # Log success
                    self.log_manager.info(
                        platform="agent_loop",
                        status="success",
                        message=f"Successfully processed message for agent {agent_id}",
                        metadata={
                            "agent_id": agent_id,
                            "message_id": msg_id
                        }
                    )
                else:
                    # Log error for invalid content
                    self.log_manager.error(
                        platform="agent_loop",
                        status="error",
                        message=f"Invalid message content for agent {agent_id}",
                        metadata={
                            "agent_id": agent_id,
                            "message_id": msg_id
                        }
                    )
                    
                    # Log error to Dreamscribe
                    error_fragment = {
                        "timestamp": time.time(),
                        "agent_id": agent_id,
                        "content": "Invalid message content",
                        "context": {
                            "source": "agent_loop",
                            "type": "task_completed",
                            "status": "error",
                            "message_id": msg_id,
                            "task_id": msg.get('task_id', 'unknown')
                        }
                    }
                    self.dreamscribe.ingest_devlog(error_fragment)
                    
            except Exception as e:
                # Log error
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
                
                # Log error to Dreamscribe
                error_fragment = {
                    "timestamp": time.time(),
                    "agent_id": agent_id,
                    "content": str(e),
                    "context": {
                        "source": "agent_loop",
                        "type": "task_completed",
                        "status": "error",
                        "message_id": msg_id,
                        "task_id": msg.get('task_id', 'unknown')
                    }
                }
                self.dreamscribe.ingest_devlog(error_fragment)
                
        # Clear the inbox after processing all messages
        inbox_file = self.inbox_path / agent_id / "inbox.json"
        if inbox_file.exists():
            save_json(inbox_file, [])

    def load_inbox(self, inbox_file: str) -> List[Dict]:
        """Load inbox from file."""
        return load_json(inbox_file, default=[])

    def save_inbox(self, inbox_file: str, inbox: List[Dict]) -> None:
        """Save inbox to file."""
        save_json(inbox_file, inbox)

async def start_agent_loops() -> None:
    """Start the agent loops."""
    controller = AgentController()  # Create controller instance
    loop = AgentLoop(controller)
    await loop.run()

if __name__ == "__main__":
    start_agent_loops() 
