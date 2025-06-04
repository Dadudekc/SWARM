"""
Cell Phone Interface

Provides a cell phone interface for agent communication, including both programmatic
and command-line interfaces.
"""

import logging
import argparse
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from .persistent_queue import PersistentQueue
from .messaging.common import Message, MessageMode

logger = logging.getLogger('cell_phone')

class CellPhone:
    """Base class for cell phone communication between agents."""
    
    _instance: Optional['CellPhone'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def reset_singleton(cls) -> None:
        """Reset the singleton instance for testing."""
        if cls._instance:
            cls._instance.shutdown()
        cls._instance = None
    
    def __init__(self):
        """Initialize the cell phone interface."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.queue = PersistentQueue()
            self.message_history = []
            self.message_statuses = {}  # Track message statuses per agent
            logger.info("Cell phone interface initialized")
    
    def send_message(self, to_agent: str, content: str, mode: str = "NORMAL", priority: int = 0) -> bool:
        """Send a message to an agent.
        
        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode (NORMAL, PRIORITY, BULK, etc.)
            priority: Message priority (0-5)
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Validate agent name
            if not to_agent or not isinstance(to_agent, str):
                raise ValueError("Invalid agent name")
            if not to_agent.startswith("Agent-"):
                raise ValueError("Agent name must start with 'Agent-'")
                
            # Accept SYSTEM as alias for SELF_TEST for test compatibility
            mode_key = mode.upper()
            if mode_key == "SYSTEM":
                mode_enum = MessageMode.SELF_TEST
            else:
                try:
                    mode_enum = MessageMode[mode_key]
                except (KeyError, AttributeError):
                    raise ValueError(f"Invalid message mode. Must be one of: {', '.join(m.name for m in MessageMode)}")
                
            # Validate message content
            if not content or not isinstance(content, str):
                raise ValueError("Message content must be a non-empty string")
                
            # Validate priority
            if not isinstance(priority, int) or priority < 0 or priority > 5:
                raise ValueError("Priority must be an integer between 0 and 5")
                
            msg = Message(
                from_agent="system",
                to_agent=to_agent,
                content=content,
                mode=mode_enum,
                priority=priority,
                timestamp=datetime.now(),
                status="queued"
            )
            
            success = self.queue.add_message(msg.to_dict())
            if success:
                self.message_history.append(msg.to_dict())
                self.message_statuses[to_agent] = "queued"
                logger.info(f"Message queued from system to {to_agent}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_message_status(self, agent_id: str) -> Dict[str, Any]:
        """Get message status for a specific agent.
        
        Args:
            agent_id: ID of the agent to get status for
            
        Returns:
            Dict containing message status information
        """
        try:
            status = self.queue.get_status()
            agent_messages = [msg for msg in self.message_history if msg.get('to_agent') == agent_id]
            return {
                "status": self.message_statuses.get(agent_id, "unknown"),
                "message_history": agent_messages,
                "queue_size": len(agent_messages)
            }
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return {"status": "error", "message_history": [], "queue_size": 0}
    
    def get_message_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get message history for a specific agent.
        
        Args:
            agent_id: ID of the agent to get history for
            
        Returns:
            List of message dictionaries
        """
        try:
            return [msg for msg in self.message_history if msg.get('to_agent') == agent_id]
        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get current message queue status."""
        status = self.queue.get_status()
        status.update({
            "message_history": self.message_history,
            "last_message": self.message_history[-1] if self.message_history else None
        })
        return status
    
    def clear_messages(self, agent_id: Optional[str] = None) -> None:
        """Clear messages from the queue."""
        if agent_id:
            self.queue.clear_agent(agent_id)
            self.message_history = [msg for msg in self.message_history if msg["to_agent"] != agent_id]
            logger.info(f"Messages cleared for {agent_id}")
        else:
            self.queue.clear()
            self.message_history = []
            logger.info("All messages cleared")
    
    def shutdown(self) -> None:
        """Shutdown the cell phone interface."""
        try:
            self.queue.shutdown()
            self.message_history.clear()  # Clear message history
            self.message_statuses.clear()  # Clear message statuses
            logger.info("Cell phone interface shut down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

class CaptainPhone(CellPhone):
    """Special phone interface for the captain to communicate with agents."""
    
    def __init__(self):
        """Initialize the captain's phone."""
        super().__init__()
        self.captain_id = "Captain"
        self.agent_status = {}  # Track agent status
        self.response_timeout = 30  # Default timeout in seconds
        self.response_dir = Path("responses")  # Directory to save responses
        self.response_dir.mkdir(exist_ok=True)
        logger.info("Captain's phone initialized")
    
    def send_message(self, to_agent: str, content: str, mode: str = "normal", priority: int = 0) -> bool:
        """Send a message from the captain to an agent and wait for response."""
        try:
            # Send the message
            success = super().send_message(to_agent, content, mode, priority, from_agent=self.captain_id)
            if not success:
                return False
                
            # Start monitoring for response
            return self._monitor_response(to_agent)
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False
    
    def _monitor_response(self, to_agent: str) -> bool:
        """Monitor for agent response with timeout."""
        import time
        start_time = time.time()
        last_message_count = len(self.message_history)
        
        while time.time() - start_time < self.response_timeout:
            # Check if we got a new message
            if len(self.message_history) > last_message_count:
                # Found a response
                response = self.message_history[-1]
                if response["from_agent"] == to_agent:
                    # Save the response
                    self._save_response(to_agent, response)
                    return True
            
            time.sleep(0.5)  # Check every half second
        
        logger.warning(f"Response timeout for {to_agent}")
        return False
    
    def _save_response(self, agent_id: str, response: Dict[str, Any]) -> None:
        """Save agent response to file."""
        try:
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{agent_id}_{timestamp}.json"
            filepath = self.response_dir / filename
            
            # Save response
            import json
            with open(filepath, 'w') as f:
                json.dump(response, f, indent=2, default=str)
            
            logger.info(f"Saved response from {agent_id} to {filepath}")
            
            # Update agent status
            self.update_agent_status(agent_id, "responded")
            
        except Exception as e:
            logger.error(f"Error saving response: {e}")
    
    def set_response_timeout(self, seconds: int) -> None:
        """Set timeout for waiting for responses."""
        if seconds < 1:
            raise ValueError("Timeout must be at least 1 second")
        self.response_timeout = seconds
        logger.info(f"Response timeout set to {seconds} seconds")
    
    def get_saved_responses(self, agent_id: Optional[str] = None) -> List[Path]:
        """Get list of saved response files."""
        if agent_id:
            return list(self.response_dir.glob(f"{agent_id}_*.json"))
        return list(self.response_dir.glob("*.json"))
    
    def clear_saved_responses(self, agent_id: Optional[str] = None) -> None:
        """Clear saved response files."""
        files = self.get_saved_responses(agent_id)
        for file in files:
            try:
                file.unlink()
                logger.info(f"Deleted response file: {file}")
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")
    
    def broadcast_message(self, content: str, mode: str = "normal", priority: int = 0) -> bool:
        """Send a message to all agents."""
        try:
            # Get list of all agents
            agents = self.list_agents()
            success = True
            
            # Send to each agent
            for agent in agents:
                if not super().send_message(agent, content, mode, priority, from_agent=self.captain_id):
                    success = False
                    logger.error(f"Failed to broadcast to {agent}")
            
            return success
        except Exception as e:
            logger.error(f"Broadcast failed: {e}")
            return False
    
    def list_agents(self) -> List[str]:
        """Get list of all available agents."""
        # Get unique agent IDs from message history
        agents = set()
        for msg in self.message_history:
            if msg["to_agent"].startswith("Agent-"):
                agents.add(msg["to_agent"])
        return sorted(list(agents))
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a specific agent."""
        if agent_id not in self.agent_status:
            self.agent_status[agent_id] = {
                "last_message": None,
                "message_count": 0,
                "status": "unknown"
            }
        return self.agent_status[agent_id]
    
    def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update status of a specific agent."""
        if agent_id not in self.agent_status:
            self.agent_status[agent_id] = {}
        self.agent_status[agent_id]["status"] = status
        logger.info(f"Updated status for {agent_id}: {status}")

def send_message(to_agent: str, message: str, priority: int = 0, mode: MessageMode = MessageMode.NORMAL) -> bool:
    """Send a message to an agent using the cell phone interface.
    
    Args:
        to_agent: The recipient agent ID
        message: The message content
        priority: Message priority (0-5)
        mode: The message mode
        
    Returns:
        bool: True if message was successfully queued
        
    Raises:
        ValueError: If priority is invalid or message is empty
    """
    cell_phone = CellPhone()
    return cell_phone.send_message(to_agent, message, mode.value, priority)

# CLI Interface
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Send messages to agents")
    parser.add_argument("--to", required=True, help="Recipient agent ID")
    parser.add_argument("--message", help="Message content")
    parser.add_argument("--priority", type=int, default=0, help="Message priority (0-5)")
    parser.add_argument("--mode", choices=[m.name for m in MessageMode], default="NORMAL", help="Message mode")
    parser.add_argument("--welcome", action="store_true", help="Send welcome message")
    return parser.parse_args()

def validate_priority(priority: int) -> bool:
    """Validate message priority."""
    return 0 <= priority <= 5

def cli_main():
    """Main entry point for CLI interface."""
    args = parse_args()
    
    # Validate priority
    if not validate_priority(args.priority):
        print("Error: Priority must be between 0 and 5", file=sys.stderr)
        sys.exit(1)
    
    # Determine message content
    if args.welcome:
        message = """Welcome to Dream.OS! You are now part of our agent network.
        
Your initial tasks:
1. Initialize your core systems
2. Establish communication channels
3. Begin monitoring your assigned domain
4. Report your status when ready

Let's begin your integration into the Dream.OS ecosystem."""
    elif args.message:
        message = args.message
    else:
        print("Error: Either --message or --welcome must be specified", file=sys.stderr)
        sys.exit(1)
    
    # Send message
    try:
        mode = MessageMode[args.mode]
        success = send_message(args.to, message, args.priority, mode)
        if not success:
            print(f"Error: Message could not be queued", file=sys.stderr)
            sys.exit(1)
        print(f"Message sent to {args.to}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli_main() 