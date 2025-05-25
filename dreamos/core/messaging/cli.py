"""
CLI Module

Provides command-line interface for the Dream.OS messaging system.
"""

import logging
import argparse
import sys
from typing import Optional, Dict, Any
from datetime import datetime

from .message import Message, MessageMode
from .processor import MessageProcessor

logger = logging.getLogger('messaging.cli')

class MessageCLI:
    """Command-line interface for messaging."""
    
    def __init__(self, processor: Optional[MessageProcessor] = None):
        """Initialize the message CLI.
        
        Args:
            processor: Optional message processor instance
        """
        self.processor = processor or MessageProcessor()
        self._parser = self._create_parser()
        
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI.
        
        Args:
            args: Optional command-line arguments
            
        Returns:
            int: Exit code
        """
        try:
            # Parse arguments
            parsed_args = self._parser.parse_args(args)
            
            # Handle command
            if parsed_args.command == 'send':
                return self._handle_send(parsed_args)
            elif parsed_args.command == 'status':
                return self._handle_status(parsed_args)
            elif parsed_args.command == 'clear':
                return self._handle_clear(parsed_args)
            else:
                self._parser.print_help()
                return 1
                
        except Exception as e:
            logger.error(f"CLI error: {e}")
            return 1
            
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser.
        
        Returns:
            ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description='Dream.OS Message CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add subparsers for commands
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Send command
        send_parser = subparsers.add_parser('send', help='Send a message')
        send_parser.add_argument('from_agent', help='Source agent ID')
        send_parser.add_argument('to_agent', help='Target agent ID')
        send_parser.add_argument('content', help='Message content')
        send_parser.add_argument('--mode', choices=[m.name for m in MessageMode],
                               default=MessageMode.NORMAL.name,
                               help='Message mode')
        send_parser.add_argument('--priority', type=int, choices=range(6),
                               default=0, help='Message priority (0-5)')
        send_parser.add_argument('--metadata', help='Message metadata (JSON)')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Get message status')
        status_parser.add_argument('--json', action='store_true',
                                 help='Output in JSON format')
        
        # Clear command
        clear_parser = subparsers.add_parser('clear', help='Clear messages')
        clear_parser.add_argument('--agent', help='Clear messages for specific agent')
        
        return parser
        
    def _handle_send(self, args: argparse.Namespace) -> int:
        """Handle send command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            int: Exit code
        """
        try:
            # Create message
            message = Message(
                from_agent=args.from_agent,
                to_agent=args.to_agent,
                content=args.content,
                mode=MessageMode[args.mode],
                priority=args.priority,
                metadata=self._parse_metadata(args.metadata)
            )
            
            # Send message
            success = self.processor.send_message(message)
            if not success:
                logger.error("Failed to send message")
                return 1
                
            print(f"Message sent from {args.from_agent} to {args.to_agent}")
            return 0
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return 1
            
    def _handle_status(self, args: argparse.Namespace) -> int:
        """Handle status command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            int: Exit code
        """
        try:
            # Get status
            status = self.processor.get_status()
            
            # Output status
            if args.json:
                import json
                print(json.dumps(status, indent=2))
            else:
                print(f"Processor running: {status['is_running']}")
                print(f"Queue size: {status['queue_status']['queue_size']}")
                print(f"History size: {status['queue_status']['history_size']}")
                print("\nRecent messages:")
                for msg in status['queue_status']['recent_messages']:
                    print(f"  {msg['message']['from_agent']} -> {msg['message']['to_agent']}: {msg['message']['content']}")
                    
            return 0
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return 1
            
    def _handle_clear(self, args: argparse.Namespace) -> int:
        """Handle clear command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            int: Exit code
        """
        try:
            # Clear messages
            self.processor.queue.clear(args.agent)
            
            # Output result
            if args.agent:
                print(f"Cleared messages for agent {args.agent}")
            else:
                print("Cleared all messages")
                
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            return 1
            
    def _parse_metadata(self, metadata_str: Optional[str]) -> Dict[str, Any]:
        """Parse metadata JSON string.
        
        Args:
            metadata_str: JSON string
            
        Returns:
            Dict containing metadata
        """
        if not metadata_str:
            return {}
            
        try:
            import json
            return json.loads(metadata_str)
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            return {} 