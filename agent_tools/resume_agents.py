#!/usr/bin/env python3

"""resume_agents.py

CLI (and optional GUI) wrapper around the *Agent Restart/Resumer* automation.

This utility makes it easy to restart ChatGPT desktop agents (1-4 by default)
**and** send them an initial resume prompt.  Under the hood it re–uses the
existing `tools.core.resume.agent_restart` helpers so we do *not* duplicate the
low-level PyAutoGUI logic.

Usage (CLI) ───────────────────────────────────────────────────────────────────

# Restart Agent-1 .. Agent-4 with the built-in default message
python resume_agents.py

# Restart a subset with a custom prompt string
python resume_agents.py --agents Agent-2,Agent-4 --prompt "Please resume testing."

# Same as above but read the prompt from a text file
python resume_agents.py --prompt-file {{ RESUME SEQUENCE  {{agent_id}}

1. Sync with your inbox  agent_tools/mailbox/{{agent_id}}/inbox.json
2. Continue next pending task (or self-assign if empty).
3. Re-read docs/onboarding/00_agent_onboarding.md, then docs/onboarding/01_agent_core.md-04_advanced_topics.md if context is lost.
4. Remember:
    Search first, reuse existing utilities (core/utils, shared modules).
        No code duplication  ever.
            Log every major step in your devlog.
            
            Reply "READY (cycle {{cycle_count}}) once you are active."}}prompts/resume.txt

# Pop up a small Tkinter window to choose / write the prompt interactively
python resume_agents.py --gui
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

# External runtime dependency (already used elsewhere in the project)
import pyautogui  # noqa: F401  # imported for side-effects (mouse / keyboard)

# Re-use existing restart helpers – honour the reuse-first rule ✅
from tools.core.resume import agent_restart as _ar

logger = logging.getLogger("agent_tools.resume_agents")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _resolve_prompt(cli_prompt: str | None, file_path: str | None) -> str | None:
    """Return the prompt text based on CLI options (or *None* for default)."""
    if cli_prompt and file_path:
        raise SystemExit("Use either --prompt or --prompt-file (not both)")
    if cli_prompt:
        return cli_prompt
    if file_path:
        p = Path(file_path).expanduser()
        if not p.is_file():
            raise SystemExit(f"[resume_agents] Prompt file not found – {p}")
        return p.read_text(encoding="utf-8")
    return None  # fall back to _ar.send_initial_message default


def _run_sequence(agents: List[str], prompt: str | None, delay: float) -> None:
    logger.info("Starting resume sequence for: %s", ", ".join(agents))

    # Monkey-patch approach identical to tools/core/resume/resume_integration_runner
    original_write = None
    if prompt is not None:
        original_write = _ar.pyautogui.write  # type: ignore[attr-defined]

        def _patched_write(text: str, *a, **kw):  # noqa: ANN001
            return original_write(prompt)  # type: ignore[misc]

        _ar.pyautogui.write = _patched_write  # type: ignore[attr-defined]

    for agent in agents:
        if not _ar.restart_agent(agent):
            logger.error("Failed to restart %s – skipping", agent)
            continue
        pyautogui.sleep(delay)  # small pause

        if not _ar.send_initial_message(agent):
            logger.error("Failed to send prompt to %s", agent)
        pyautogui.sleep(delay)

    # Restore original write fn if we patched it
    if original_write is not None:
        _ar.pyautogui.write = original_write  # type: ignore[attr-defined]

    logger.info("✅ Resume sequence complete.")


# ---------------------------------------------------------------------------
# Optional: very small Tkinter GUI to select / enter prompt text
# ---------------------------------------------------------------------------

def _launch_gui(default_agents: List[str]):  # noqa: D401
    try:
        import tkinter as tk
        from tkinter import messagebox, scrolledtext, ttk
    except ImportError as exc:
        raise SystemExit(f"Tkinter not available: {exc}. Install or use CLI mode.") from exc

    root = tk.Tk()
    root.title("Resume Agents")

    # Agents selection (checkboxes)
    agents_vars = {a: tk.BooleanVar(value=True) for a in default_agents}

    agents_frame = ttk.LabelFrame(root, text="Agents")
    agents_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    for idx, (agent, var) in enumerate(agents_vars.items()):
        ttk.Checkbutton(agents_frame, text=agent, variable=var).grid(row=idx, column=0, sticky="w")

    # Prompt entry area
    prompt_frame = ttk.LabelFrame(root, text="Resume Prompt")
    prompt_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    prompt_text = scrolledtext.ScrolledText(prompt_frame, width=40, height=10)
    prompt_text.pack(fill="both", expand=True)

    # Control buttons
    def _on_run():
        selected = [a for a, var in agents_vars.items() if var.get()]
        text = prompt_text.get("1.0", "end").strip() or None
        if not selected:
            messagebox.showwarning("No agents", "Please select at least one agent to resume.")
            return
        root.destroy()  # close GUI before running automation
        _run_sequence(selected, text, delay=2.0)

    ttk.Button(root, text="Run", command=_on_run).grid(row=1, column=0, columnspan=2, pady=(0, 10))

    root.mainloop()


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    parser = argparse.ArgumentParser(description="Resume specified agents and send initial prompt")
    parser.add_argument(
        "--agents",
        default="Agent-1,Agent-2,Agent-3,Agent-4",
        help="Comma-separated list of agent IDs (default 1-4)",
    )
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Custom prompt text to send to each agent")
    prompt_group.add_argument("--prompt-file", help="Path to text file containing the prompt")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay (seconds) between actions [default 2]")
    parser.add_argument("--gui", action="store_true", help="Launch a small GUI instead of CLI flags")

    opts = parser.parse_args()

    agents = [a.strip() for a in opts.agents.split(",") if a.strip()]
    if not agents:
        raise SystemExit("--agents list is empty")

    if opts.gui:
        _launch_gui(agents)
        return

    prompt = _resolve_prompt(opts.prompt, opts.prompt_file)
    _run_sequence(agents, prompt, opts.delay)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted by user") 