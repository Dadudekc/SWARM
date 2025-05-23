"""
CLI interface for sending messages to agents.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
from dreamos.core.cell_phone import send_message, MessageMode

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

def main():
    """Main entry point."""
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
        
        # Print success message
        print(f"Message sent to {args.to}")
        print(message)  # Print the message content
        if args.mode != "NORMAL":
            print(f"[{args.mode}]")
        print(f"Status: Message queued with priority {args.priority}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 