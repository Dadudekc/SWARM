"""
Command Line Interface

Provides a command-line interface for agent communication.
"""

import argparse
import sys
import asyncio
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import pyautogui
import os
import logging

from .utils.core_utils import (
    atomic_write,
    safe_read,
    safe_write,
    load_json,
    save_json,
    ensure_dir,
    read_json,
    write_json,
    read_yaml,
    write_yaml,
    ensure_directory_exists,
    load_yaml,
    get_timestamp,
    format_duration,
    is_valid_uuid,
)
from dreamos.core.utils import load_json
from .shared.coordinate_utils import load_coordinates as util_load_coordinates
from dreamos.core.log_manager import LogManager, LogConfig, LogLevel
from .config.config_manager import ConfigManager
from dreamos.core.messaging.message_processor import MessageProcessor
from dreamos.core.messaging.common import Message, MessageMode
from dreamos.core.messaging.enums import MessagePriority

# Add the project root to Python path when running as standalone script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

# Version information
__version__ = "1.0.0"

# Runtime directory
RUNTIME_DIR = Path("runtime")
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

# Initialize logging
log_manager = LogManager(
    LogConfig(level=LogLevel.INFO, log_dir="logs/cli", platforms={"cli": "cli.log"})
)
logger = log_manager


class MessageCLI:
    """Command-line interface for agent communication."""

    def __init__(self):
        """Initialize the CLI interface."""
        self.processor = MessageProcessor(str(RUNTIME_DIR))
        logger.info("CLI interface initialized")

    def send_message(
        self, to_agent: str, content: str, mode: MessageMode = MessageMode.NORMAL
    ) -> bool:
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
                status="queued",
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


def direct_send_message(to_agent: str, message: str, mode: str = "NORMAL") -> bool:
    """Send a message directly to the UI using automation."""
    try:
        coords_file = Path("config/cursor_agent_coords.json")
        coordinates = util_load_coordinates(coords_file)

        if not coordinates or to_agent not in coordinates:
            logger.error(f"No coordinates found for {to_agent}")
            print(f"[ERROR] No coordinates found for {to_agent}")
            return False

        coords = coordinates[to_agent]
        input_box = (coords["input_box"]["x"], coords["input_box"]["y"])
        pyautogui.moveTo(input_box[0], input_box[1])
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.write(message)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.5)
        logger.info(f"Message sent directly to {to_agent}")
        return True

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        print(f"Error: {e}")
        return False


async def _bus_publish(
    topic: str, content: str, sender: str, priority: MessagePriority, mode: MessageMode
) -> str:
    bus = AgentBus()
    return await bus.publish(
        topic=topic,
        content=content,
        sender=sender,
        priority=priority,
        mode=mode,
    )


def bus_send_message(
    to_agent: str,
    message: str,
    priority: MessagePriority = MessagePriority.NORMAL,
    mode: MessageMode = MessageMode.NORMAL,
    sender: str = "system",
) -> str:
    """Publish a message to the AgentBus synchronously."""
    return asyncio.run(_bus_publish(to_agent, message, sender, priority, mode))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Send messages to agents")
    parser.add_argument("--to", help="Recipient agent ID")
    parser.add_argument("--message", help="Message content")
    parser.add_argument(
        "--priority", type=int, default=0, help="Message priority (0-5)"
    )
    parser.add_argument(
        "--mode",
        choices=[m.name for m in MessageMode],
        default="NORMAL",
        help="Message mode",
    )
    parser.add_argument("--welcome", action="store_true", help="Send welcome message")
    parser.add_argument(
        "--version", action="store_true", help="Show version information"
    )
    parser.add_argument(
        "--direct", action="store_true", help="Send using direct automation"
    )
    parser.add_argument("--bus", action="store_true", help="Send via AgentBus")
    return parser.parse_args()


def validate_priority(priority: int) -> bool:
    """Validate message priority."""
    return 0 <= priority <= 5


def load_coordinates(coords_file: str) -> Dict:
    """Load coordinates from file."""
    coordinates = util_load_coordinates(coords_file)
    return coordinates if coordinates else {}


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

    # Send message using selected method
    try:
        mode_enum = MessageMode[args.mode]

        if args.direct:
            success = direct_send_message(args.to, message, args.mode)
            if success:
                print(f"Direct message sent to {args.to}")
            else:
                print("Error: Message could not be sent", file=sys.stderr)
                sys.exit(1)
            return

        if args.bus:
            priority_enum = MessagePriority(min(args.priority, 3))
            msg_id = bus_send_message(args.to, message, priority_enum, mode_enum)
            print(f"Bus message sent with ID: {msg_id}")
            return

        cli = MessageCLI()
        success = cli.send_message(args.to, message, mode_enum)
        if not success:
            print("Error: Message could not be sent", file=sys.stderr)
            sys.exit(1)
        print(f"Message sent to {args.to}")
        print(message)
        if mode_enum != MessageMode.NORMAL:
            print(f"[{mode_enum.name}]")
        print("Status: queued")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# Create singleton instance
_cli = MessageCLI()


def send_message(
    to_agent: str, content: str, mode: MessageMode = MessageMode.NORMAL
) -> bool:
    """Send a message to an agent.

    Args:
        to_agent: The recipient agent ID
        content: The message content
        mode: The message mode

    Returns:
        bool: True if message was successfully sent
    """
    return _cli.send_message(to_agent, content, mode)


def get_status() -> dict:
    """Get current message status.

    Returns:
        Dict containing message statistics
    """
    return _cli.get_status()


def clear_messages(agent_id: Optional[str] = None) -> None:
    """Clear messages.

    Args:
        agent_id: Optional agent ID to clear messages for. If None, clears all messages.
    """
    _cli.clear_messages(agent_id)


def shutdown() -> None:
    """Clean up resources."""
    _cli.shutdown()


__all__ = [
    "MessageCLI",
    "send_message",
    "get_status",
    "clear_messages",
    "shutdown",
    "direct_send_message",
    "bus_send_message",
    "parse_args",
    "validate_priority",
    "load_coordinates",
    "cli_main",
]

if __name__ == "__main__":
    cli_main()
