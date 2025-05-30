"""
Command Line Interface

Provides a command-line interface for agent communication.
"""

import logging
import argparse
import sys
import os
from typing import Optional
from datetime import datetime

# Add the project root to Python path when running as standalone script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from dreamos.core.message_processor import MessageProcessor
    from dreamos.core.messaging.types import Message, MessageMode
else:
    from .message_processor import MessageProcessor
    from .messaging.types import Message, MessageMode

# Version information
__version__ = "1.0.0"

logger = logging.getLogger('cli')

class MessageCLI:
    """Command-line interface for agent communication."""
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.processor = MessageProcessor()
        logger.info("CLI interface initialized")
    
    def send_message(self, to_agent: str, content: str, mode: MessageMode = MessageMode.NORMAL) -> bool:
        """Send a message to an agent.
        
        Args:
            to_agent: The recipient agent ID
            content: The message content
            mode: The message mode
            
        Returns:
            bool: True if message was successfully sent
        """
        try:
            message = Message(
                from_agent="CLI",
                to_agent=to_agent,
                content=content,
                mode=mode,
                priority=0,
                timestamp=datetime.now(),
                status="queued"
            )
            return self.processor.process_message(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get current message status.
        
        Returns:
            Dict containing message statistics
        """
        return self.processor.get_status()
    
    def clear_messages(self, agent_id: Optional[str] = None) -> None:
        """Clear messages.
        
        Args:
            agent_id: Optional agent ID to clear messages for. If None, clears all messages.
        """
        self.processor.clear_messages(agent_id)
    
    def shutdown(self) -> None:
        """Clean up resources."""
        self.processor.shutdown()
        logger.info("CLI interface shut down")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Send messages to agents")
    parser.add_argument("--to", help="Recipient agent ID")
    parser.add_argument("--message", help="Message content")
    parser.add_argument("--priority", type=int, default=0, help="Message priority (0-5)")
    parser.add_argument("--mode", choices=[m.name for m in MessageMode], default="NORMAL", help="Message mode")
    parser.add_argument("--welcome", action="store_true", help="Send welcome message")
    parser.add_argument("--version", action="store_true", help="Show version information")
    return parser.parse_args()

def validate_priority(priority: int) -> bool:
    """Validate message priority."""
    return 0 <= priority <= 5

def cli_main():
    """Main entry point for CLI interface."""
    args = parse_args()
    
    # Handle version command
    if args.version:
        print(f"Dream.OS CLI version {__version__}")
        sys.exit(0)
    
    # Validate required arguments for message sending
    if not args.to:
        print("Error: --to argument is required for sending messages", file=sys.stderr)
        sys.exit(1)
    
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
        cli = MessageCLI()
        success = cli.send_message(args.to, message, mode)
        if not success:
            print(f"Error: Message could not be sent", file=sys.stderr)
            sys.exit(1)
        print(f"Message sent to {args.to}")
        # Print message content
        print(message)
        # Print mode if not NORMAL
        if mode != MessageMode.NORMAL:
            print(f"[{mode.name}]")
        # Print Status line (placeholder)
        print("Status: queued")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli_main() 