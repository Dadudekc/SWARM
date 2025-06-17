"""
Agent Restart System

Restarts agents using Ctrl+N and sends initial messages to their input boxes.
Ensures agents know where to respond in the message area.
"""

import time
import logging
import pyautogui
import json
from pathlib import Path
import os
from argparse import ArgumentParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_restart')

# ---------------------------------------------------------------------------
# Basic resilience constants
# ---------------------------------------------------------------------------

MAX_RETRIES: int = 3  # simple retry cap for UI flakiness

# EDIT START – profile-aware coordinate support
# Determine coordinates file based on *UI_PROFILE* env or CLI flag
_profile_env = os.getenv("UI_PROFILE") or os.getenv("PROFILE") or "windows"
_parser = ArgumentParser(add_help=False)
_parser.add_argument("--profile", choices=["windows", "mac"], default=_profile_env)
_known, _ = _parser.parse_known_args()
_ACTIVE_PROFILE: str = _known.profile  # immutable runtime constant

# Coordinates search order (new –> legacy)
_NEW_COORDS_PATH = Path("config/bridge/agent_coords.json")
_LEGACY_COORDS_PATH = Path("runtime/config/cursor_agent_coords.json")

# EDIT START – fallback prompt (tests expect this to exist)
DEFAULT_RESUME_PROMPT: str = "{agent_name}: Restarting session."  # minimal placeholder
# EDIT END

def _load_from_new(profile: str) -> dict | None:  # noqa: D401
    if not _NEW_COORDS_PATH.exists():
        return None
    with open(_NEW_COORDS_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # If profile section exists, return it otherwise fall back to raw dict
    return data.get(profile) if isinstance(data, dict) else data

# EDIT END

def load_coordinates():  # noqa: D401
    """Load agent-coordinate mapping for the active UI profile.

    Order of precedence:
        1. *config/bridge/agent_coords.json* (profile section)
        2. Legacy *runtime/config/cursor_agent_coords.json*
    """
    # 1) try profile-aware file
    coords = _load_from_new(_ACTIVE_PROFILE)
    if coords:
        logger.debug("Loaded coordinates for profile '%s' from new path", _ACTIVE_PROFILE)
        return coords

    # 2) fall back to legacy single-profile mapping
    with open(_LEGACY_COORDS_PATH, "r", encoding="utf-8") as fh:
        logger.debug("Falling back to legacy coordinate file: %s", _LEGACY_COORDS_PATH)
        return json.load(fh)

def _restart_once(agent_name: str) -> bool:  # noqa: D401 – internal helper
    """Single attempt to restart *agent_name*."""
    try:
        coords = load_coordinates()
        agent_coords = coords[agent_name]
        window_pos = agent_coords['initial_spot']
        pyautogui.moveTo(window_pos['x'], window_pos['y'])
        pyautogui.click()
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(2)
        logger.info(f"Restarted {agent_name}")
        return True
    except Exception as e:
        logger.error(f"Error restarting {agent_name}: {e}")
        return False

def restart_agent(agent_name: str):
    """Restart an agent using Ctrl+N."""
    for _ in range(MAX_RETRIES):
        if _restart_once(agent_name):
            return True
        logger.warning("Retrying restart for %s", agent_name)
        time.sleep(1)
    return False

def _send_once(agent_name: str, prompt: str | None, delay: float) -> bool:  # noqa: D401
    try:
        coords = load_coordinates()
        agent_coords = coords[agent_name]
        input_box = agent_coords['input_box_initial']
        pyautogui.moveTo(input_box['x'], input_box['y'])
        pyautogui.click()
        time.sleep(delay)
        if prompt is not None:
            message = prompt
        else:
            message = f"{DEFAULT_RESUME_PROMPT.format(agent_name=agent_name)} Your sequence position is: "
            if agent_name == "Agent-1":
                message += "1st"
            elif agent_name == "Agent-2":
                message += "2nd"
            elif agent_name == "Agent-4":
                message += "3rd"
            elif agent_name == "Agent-6":
                message += "4th"
            elif agent_name == "Agent-7":
                message += "5th"
            elif agent_name == "Agent-8":
                message += "6th"
        pyautogui.write(message, interval=0.015)
        time.sleep(delay)
        pyautogui.press('enter')
        logger.info(f"Sent initial message to {agent_name}")
        return True
    except Exception as e:
        logger.error(f"Error sending message to {agent_name}: {e}")
        return False

def send_initial_message(agent_name: str, prompt: str | None = None, *, delay: float = 0.5) -> bool:
    """Retry wrapper around *_send_once*."""
    for _ in range(MAX_RETRIES):
        if _send_once(agent_name, prompt, delay):
            return True
        logger.warning("Retrying send_initial_message for %s", agent_name)
        time.sleep(1)
    return False

def main():
    """Main function to restart all agents and send initial messages."""
    logger.info("Starting Agent Restart System")
    
    # Sequence of agents
    agents = ["Agent-1", "Agent-2", "Agent-4", "Agent-6", "Agent-7", "Agent-8"]
    
    for agent in agents:
        logger.info(f"Processing {agent}")
        
        # Restart agent
        if restart_agent(agent):
            time.sleep(2)  # Wait for restart to complete
            
            # Send initial message
            if send_initial_message(agent):
                time.sleep(1)  # Wait between agents
            else:
                logger.error(f"Failed to send initial message to {agent}")
        else:
            logger.error(f"Failed to restart {agent}")
            
        # Wait between agents
        time.sleep(2)
    
    logger.info("Agent Restart System completed")

if __name__ == "__main__":
    main() 
