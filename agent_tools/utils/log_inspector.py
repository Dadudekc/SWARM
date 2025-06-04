#!/usr/bin/env python3
"""Simple CLI tool for inspecting log files managed by :class:`LogManager`."""

import argparse
from datetime import datetime
import logging
from typing import Optional

from social.utils.log_manager import LogManager, LogLevel


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Inspect SWARM log files")
    parser.add_argument(
        "--platform",
        choices=["system", "discord", "voice", "agent"],
        help="Filter logs by platform",
    )
    parser.add_argument(
        "--level",
        choices=[l.name for l in LogLevel],
        help="Minimum log level to show",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of log entries to display",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only show logs after this ISO timestamp",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manager = LogManager()

    start_time: Optional[datetime] = None
    if args.since:
        try:
            start_time = datetime.fromisoformat(args.since)
        except ValueError:
            logging.error("Invalid --since timestamp format")
            return

    if args.level:
        # update log level temporarily for inspection output
        manager.set_level(LogLevel[args.level])

    entries = manager.read_logs(
        platform=args.platform,
        level=args.level,
        start_time=start_time,
        limit=args.limit,
    )

    for entry in entries:
        timestamp = entry.get("timestamp")
        level = entry.get("level")
        platform = entry.get("platform")
        message = entry.get("message")
        print(f"[{timestamp}] {platform} {level}: {message}")


if __name__ == "__main__":
    main()

