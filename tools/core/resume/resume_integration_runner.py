"""Interactive integration runner for the *Agent Restart* automation.

This script executes the *real* PyAutoGUI flows defined in
`tools.core.resume.agent_restart` so you can visually confirm that:

1. The correct window / coordinates are targeted for each agent.
2. The expected initial message text appears in the input box.
3. No stray mouse movements or keystrokes occur.

Usage
-----
Run from a desktop session where the agent UI is visible *exactly* in the
positions recorded in ``runtime/config/cursor_agent_coords.json``::

    python tools/core/resume/resume_integration_runner.py [--agents Agent-1,Agent-2] [--delay 2] [--screenshots]

Options
~~~~~~~
--agents
    Comma-separated list of agent IDs to exercise (default: Agent-1,Agent-2,Agent-3,Agent-4).
--delay
    Seconds to wait **between** major actions (restart, message send).  Give
the UI time to settle.  Default: ``2``.
--screenshots
    If set, capture a PNG *after* each agent's message is sent to
    ``runtime/screenshots/<agent>_<timestamp>.png`` for later inspection.
--message
    Override the default initial message with custom text.

Safety
~~~~~~
The script prints each high-level step before it executes and pauses one second
up-front so you can abort (Ctrl-C) if something looks off.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List

import pyautogui

from tools.core.resume import agent_restart as _ar
from tools.core.resume.agent_restart import restart_agent, send_initial_message

logger = logging.getLogger("resume_integration_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _take_screenshot(agent_id: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{agent_id}_{ts}.png"
    try:
        pyautogui.screenshot(str(path))
        logger.info("📸 Screenshot saved → %s", path)
    except Exception as exc:
        logger.warning("Could not take screenshot: %s", exc)


def run_sequence(agents: List[str], delay: float, screenshots: bool, custom_msg: str | None) -> None:
    logger.info("Starting integration run for agents: %s", ", ".join(agents))
    time.sleep(1)  # Small grace period to let user abort

    for agent in agents:
        logger.info("▶ Restarting %s", agent)
        if not restart_agent(agent):
            logger.error("Failed to restart %s – skipping", agent)
            continue
        time.sleep(delay)

        logger.info("✉️  Sending initial message to %s", agent)
        if custom_msg is not None:
            original_write = _ar.pyautogui.write

            def _patched_write(text: str, *a, **kw):  # noqa: ANN001
                # replace only the dynamic portion for clarity
                return original_write(custom_msg)

            _ar.pyautogui.write = _patched_write  # type: ignore[attr-defined]

        ok = send_initial_message(agent)

        if custom_msg is not None:
            _ar.pyautogui.write = original_write  # restore

        if not ok:
            logger.error("Failed to send message to %s", agent)
            continue
        if screenshots:
            _take_screenshot(agent, Path("runtime/screenshots"))

        time.sleep(delay)

    logger.info("✅ Integration sequence complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full resume/message sequence for visual verification")
    parser.add_argument(
        "--agents",
        default="Agent-1,Agent-2,Agent-3,Agent-4",
        help="Comma-separated list of agent IDs (default: Agent-1…4)",
    )
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between steps (default 2)")
    parser.add_argument("--screenshots", action="store_true", help="Capture a screenshot after each agent")
    parser.add_argument("--message", help="Override the default initial message with custom text")
    opts = parser.parse_args()

    run_sequence(
        [a.strip() for a in opts.agents.split(",") if a.strip()],
        opts.delay,
        opts.screenshots,
        opts.message,
    ) 