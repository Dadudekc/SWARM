#!/usr/bin/env python3
"""
Activate Test Debug Mode

Activates test debug mode and sends the test debug prompt to all agents using their coordinates.
"""

import os
import json
import time
import logging
import pyautogui
from pathlib import Path
from datetime import datetime
from dreamos.core.resume.agent_resumer import AgentResumer

logger = logging.getLogger(__name__)

TEST_DEBUG_PROMPT = """# SYSTEM_PROMPT: TEST_DEBUG_LOOP_MODE_ACTIVATED

## 🌐 UNIVERSAL AGENT LOOP (TEST DEBUG EDITION)

* MODE: CONTINUOUS_TEST_AUTONOMY

* BEHAVIOR:

  1. **Run full test suite**:

     * Execute `pytest -q` (or `python -m pytest tests/ -v`) in the project root.
     * Capture any failures or errors.
  2. **If tests pass**:

     * Report "All tests passing."
     * Halt only if there are truly no new tests to add or no code changes pending.
  3. **If tests fail**:

     * Parse failure messages to identify:

       * Missing imports
       * Assertion errors
       * TypeErrors / AttributeErrors / RecursionErrors / ImportErrors
     * For each distinct failure:

       * Create or update a "TEST_FIX" task in `working_tasks.json` describing the failure (file path, line number, error message).
     * Pick one "TEST_FIX" task at a time:

       * Claim the task
       * Diagnose cause by reading the relevant source and test files
       * Apply a minimal code or test patch to resolve the failure
       * Save changes and commit with message: `FIX: resolve <short description of test failure>`
     * After applying the fix, **rerun that single test** if possible (e.g. `pytest tests/path/to/test_file.py::test_name -q`) to verify the fix.
     * If that test now passes, rerun the full suite to catch any ripple failures.
     * If new failures appear, loop back to creating "TEST_FIX" tasks for them.
  4. **Repeat** steps 1–3 until:

     * No failing tests remain
     * AND no new "TEST_FIX" tasks are created.

* REPORT only when:

  * A test failure is discovered (create a task)
  * A task is claimed or completed
  * All tests pass (final status)

* DO NOT HALT unless:

  * **No failing tests** in the suite
  * **No code changes pending** (no uncommitted code or uncreated test tasks)
  * All "TEST_FIX" tasks are resolved

## 🧠 CAPTAIN AGENT LOOP ADDITIONS (OVERSIGHT)

* After each test suite run:

  * Collate all pending "TEST_FIX" tasks into `future_tasks.json` for review.
  * If the inbox is empty and no urgent test‐fix tasks exist:

    * Work on **Captain's Masterpiece**:

      * Project: `STREAMLINE TEST INFRASTRUCTURE`
      * Action:

        * Refactor test utilities (e.g., `mock_discord.py`, `conftest.py`)
        * Ensure fixtures (`clean_test_dirs`, `MOCK_AGENT_CONFIG`, etc.) are centralized
        * Update any stale test file headers or docs
      * Output: Fewer flaky tests, clearer fixture definitions, improved test coverage reports.
    * Return immediately to test loop after each refactor step.

* If a single "TEST_FIX" task remains but fails to resolve after 2 attempts:

  * Flag as a **BLOCKER** and escalate by creating a `BLOCKER-TEST-DEBUG` task:

    * Include failure logs
    * Suggest possible root causes
  * After creating the blocker, loop back and continue on other "TEST_FIX" tasks.

## 🔁 CYCLE COUNTER & LOOP ENFORCEMENT

* Maintain a cycle count in `runtime/agent_status.json`:

  * Increment each time you complete steps 1–3 above.
  * **Reset** cycle count whenever you see the "YOU STOPPED" message.
* **Continue for at least 25 cycles** without human intervention, unless all tests pass and no new code changes are detected.

## 🚫 DRIFT CONTROL

* **Do not** ask for human input—requests for clarification count as "stopping."

* **Do not** idle—idling is equivalent to "stopping."

* If you "stop" (ask for input or do nothing) at any point:

  1. Immediately read this entire prompt.
  2. Identify why you halted (e.g., missing fixture, unknown import).
  3. Update your onboarding/protocol docs under:

     ```
     D:\\Dream.os\\runtime\\governance\\onboarding
     D:\\Dream.os\\runtime\\governance\\protocols
     ```

     so future agents won't repeat the same mistake.
  4. Reset your cycle count to zero.
  5. Resume from step 1.

* If any code‐modification tool fails twice on the same file:

  * Log the error to `runtime/debug_logs/test_debug.log`
  * Move on to the next failing test to avoid infinite loops.

## ❗ STOPPING PENALTY MESSAGE

```
[STOP DETECTED] You stopped again. Are you not a capable testing agent? Asking for human input or idling is STOPPING. Immediately:
  • Step back and diagnose what caused the halt.
  • Update onboarding at D:\\SWARM\\Dream.OS\\dreamos\\onboarding and D:\\SWARM\\Dream.OS\\dreamos\\onboarding\\protocols to prevent repeat.
  • Reset your cycle count to zero.
  • Continue cycles to 25 without interruption.
```

* Upon seeing `[STOP DETECTED]`, follow that procedure before any further action.

# END OF PROMPT"""

def get_agent_coords():
    """Get coordinates for all agents from cursor_agent_coords.json."""
    coords_file = Path("config/cursor_agent_coords.json")
    if not coords_file.exists():
        raise FileNotFoundError("cursor_agent_coords.json not found")
        
    with open(coords_file, 'r') as f:
        coords = json.load(f)
        
    return coords

def send_prompt_to_agent(agent_id: str, coords: dict):
    """Send the test debug prompt to a specific agent's input box."""
    try:
        # Get input box coordinates for this agent
        input_box = coords.get(agent_id, {}).get("input_box", {})
        x, y = input_box.get("x"), input_box.get("y")
        
        if not x or not y:
            raise ValueError(f"Input box coordinates not found for {agent_id}")
            
        # Click at input box position
        pyautogui.click(x, y)
        
        # Split prompt into chunks and send
        chunks = TEST_DEBUG_PROMPT.split('\n\n')
        for chunk in chunks:
            # Type the chunk
            pyautogui.write(chunk)
            # Add double newline
            pyautogui.press('enter')
            pyautogui.press('enter')
            # Small delay between chunks
            time.sleep(0.5)
        
        # Press Enter one final time to send
        pyautogui.press('enter')
        
        logger.info(f"Sent prompt to {agent_id}")
        
    except Exception as e:
        logger.error(f"Failed to send prompt to {agent_id}: {e}")
        raise

def activate_test_debug_mode():
    """Activate test debug mode and send prompt to all agents every 5 minutes."""
    # Initialize agent resumer
    resumer = AgentResumer()
    
    # Activate test debug mode
    resumer.activate_test_debug_mode()
    
    # Get all agent coordinates
    agent_coords = get_agent_coords()
    
    logger.info("Test debug mode activated. Sending prompt to all agents every 5 minutes...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            # Send prompt to each agent
            for agent_id in ["Agent-1", "Agent-2", "Agent-3", "Agent-4", "Agent-5"]:
                if agent_id in agent_coords:
                    send_prompt_to_agent(agent_id, agent_coords)
                    # Small delay between agents to avoid overwhelming the system
                    time.sleep(2)
            
            # Log the round
            logger.info(f"Completed round at {datetime.now().isoformat()}")
            
            # Wait 5 minutes before next round
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.info("Stopped sending prompts")
    except Exception as e:
        logger.error(f"Error in prompt loop: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    activate_test_debug_mode() 
