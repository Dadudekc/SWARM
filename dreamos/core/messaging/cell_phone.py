"""
Cell Phone Interface
------------------
Provides a simplified interface to the unified message system.
"""

import logging
import argparse
import sys
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .unified_message_system import (
    UnifiedMessageSystem,
    Message,
    MessageMode,
    MessagePriority,
)

logger = logging.getLogger("dreamos.messaging.cell_phone")


class CellPhone:
    """Simplified interface to the unified message system."""

    def __init__(self, runtime_dir: Optional[Path] = None):
        """Initialize cell phone interface.

        Args:
            runtime_dir: Optional runtime directory
        """
        self.ums = UnifiedMessageSystem.instance()
        self.runtime_dir = runtime_dir

    async def send_message(
        self,
        to_agent: str,
        content: str,
        mode: str = "NORMAL",
        priority: Union[str, int] = "NORMAL",
        from_agent: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a message.

        Args:
            to_agent: Target agent ID
            content: Message content
            mode: Message mode
            priority: Message priority
            from_agent: Sender agent ID
            metadata: Additional message metadata

        Returns:
            bool: True if message was successfully sent
        """
        try:
            # Validate recipient
            if (
                not to_agent
                or not isinstance(to_agent, str)
                or not to_agent.startswith("Agent-")
            ):
                raise ValueError(
                    "Agent name must be a non-empty string starting with 'Agent-'"
                )

            # Validate content
            if not content or not isinstance(content, str):
                raise ValueError("Message content must be a non-empty string")

            # Convert/validate mode
            mode_key = mode.upper()
            if mode_key == "SYSTEM":
                message_mode = MessageMode.SELF_TEST
            else:
                message_mode = MessageMode[mode_key]

            # Convert/validate priority
            if isinstance(priority, int):
                if priority < 0 or priority > 5:
                    raise ValueError("Priority must be between 0 and 5")
                message_priority = MessagePriority(priority)
            else:
                message_priority = MessagePriority[priority.upper()]

            return await self.ums.send(
                to_agent=to_agent,
                content=content,
                mode=message_mode,
                priority=message_priority,
                from_agent=from_agent,
                metadata=metadata,
            )

        except KeyError as e:
            logger.error(f"Invalid message mode or priority: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def receive_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get pending messages for an agent.

        Args:
            agent_id: ID of agent to get messages for

        Returns:
            List[Dict[str, Any]]: List of pending messages
        """
        try:
            messages = await self.ums.receive(agent_id)
            return [
                {
                    "message_id": msg.message_id,
                    "sender_id": msg.sender_id,
                    "content": msg.content,
                    "mode": msg.mode.value,
                    "priority": msg.priority.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []

    async def get_message_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get message history.

        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Optional maximum number of messages to return

        Returns:
            List[Dict[str, Any]]: List of historical messages
        """
        try:
            messages = await self.ums.get_history(
                agent_id=agent_id, start_time=start_time, end_time=end_time, limit=limit
            )
            return [
                {
                    "message_id": msg.message_id,
                    "sender_id": msg.sender_id,
                    "recipient_id": msg.recipient_id,
                    "content": msg.content,
                    "mode": msg.mode.value,
                    "priority": msg.priority.value,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                    "status": msg.status,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error getting message history: {e}")
            return []

    async def subscribe(self, topic: str, handler: callable) -> None:
        """Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")

    async def subscribe_pattern(self, pattern: str, handler: callable) -> None:
        """Subscribe to messages matching a pattern.

        Args:
            pattern: Regex pattern to match
            handler: Callback function to handle messages
        """
        try:
            await self.ums.subscribe_pattern(pattern, handler)
        except Exception as e:
            logger.error(f"Error subscribing to pattern {pattern}: {e}")

    async def unsubscribe(self, topic: str, handler: callable) -> None:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler to remove
        """
        try:
            await self.ums.unsubscribe(topic, handler)
        except Exception as e:
            logger.error(f"Error unsubscribing from topic {topic}: {e}")

    async def unsubscribe_pattern(self, pattern: str, handler: callable) -> None:
        """Unsubscribe from a pattern.

        Args:
            pattern: Pattern to unsubscribe from
            handler: Handler to remove
        """
        try:
            await self.ums.unsubscribe_pattern(pattern, handler)
        except Exception as e:
            logger.error(f"Error unsubscribing from pattern {pattern}: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.ums.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def validate_priority(priority: int) -> bool:
    """Validate message priority."""
    return 0 <= priority <= 5


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for CLI usage."""
    parser = argparse.ArgumentParser(description="Send messages to agents")
    parser.add_argument("--to", required=True, help="Recipient agent ID")
    parser.add_argument("--message", help="Message content")
    parser.add_argument(
        "--priority", type=int, default=2, help="Message priority (0-5)"
    )
    parser.add_argument(
        "--mode",
        choices=[m.name for m in MessageMode],
        default="NORMAL",
        help="Message mode",
    )
    parser.add_argument("--welcome", action="store_true", help="Send welcome message")
    return parser.parse_args()


def send_message(
    to_agent: str,
    message: str,
    priority: Union[int, str] = MessagePriority.NORMAL.name,
    mode: str = "NORMAL",
    from_agent: str = "system",
) -> bool:
    """Convenience synchronous wrapper for ``CellPhone.send_message``."""
    phone = CellPhone()
    return asyncio.run(
        phone.send_message(
            to_agent=to_agent,
            content=message,
            mode=mode,
            priority=priority,
            from_agent=from_agent,
        )
    )


def cli_main() -> None:
    """Entry point for command line usage."""
    args = parse_args()

    if not validate_priority(args.priority):
        print("Error: Priority must be between 0 and 5", file=sys.stderr)
        sys.exit(1)

    if args.welcome:
        content = (
            "Welcome to Dream.OS! You are now part of our agent network.\n\n"
            "Your initial tasks:\n"
            "1. Initialize your core systems\n"
            "2. Establish communication channels\n"
            "3. Begin monitoring your assigned domain\n"
            "4. Report your status when ready\n\n"
            "Let's begin your integration into the Dream.OS ecosystem."
        )
        mode = "RESUME"
    else:
        if not args.message:
            print("Error: --message is required", file=sys.stderr)
            sys.exit(1)
        content = args.message
        mode = args.mode

    success = send_message(args.to, content, args.priority, mode)
    if not success:
        print("Error: Message could not be sent", file=sys.stderr)
        sys.exit(1)
    print(f"Message sent to {args.to}")


if __name__ == "__main__":
    cli_main()
