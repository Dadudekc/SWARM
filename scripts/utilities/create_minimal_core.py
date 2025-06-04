"""Utility script for generating a minimal Dream.OS distribution."""

import shutil
from pathlib import Path

# Define paths
base_dir = Path("D:/SWARM/Dream.OS")  # Source Dream.OS root
minimal_dir = base_dir.parent / "MinimalDreamOS"

# Reset minimal output dir
if minimal_dir.exists():
    shutil.rmtree(minimal_dir)
minimal_dir.mkdir()

# Core files and folders to include
core_structure = {
    "agent_tools/general_tools": ["discord_devlog.py", "agent_webhooks.json"],
    # "agent_tools/mailbox/agent-1/workspace": ["dream_weaver_llm.py"],  # Removed as missing
    "config/system": ["agent_resume.yaml"],
    "runtime/system/status": ["resume_status.json", "agent-1_heartbeat.json"],
    "dreamos/core/agent_control": [
        "agent_controller.py",
        "periodic_restart.py",
        "ui_automation.py",
        "task_manager.py",
        "devlog_manager.py",
        "cell_phone.py",
        "message.py",
    ],
    "dreamos/core": ["utils.py"],
    "": ["agent_launcher.py"],
}

skipped = []

# Copy files, skipping missing ones
for rel_path, files in core_structure.items():
    src_path = base_dir / rel_path
    dest_path = minimal_dir / rel_path
    dest_path.mkdir(parents=True, exist_ok=True)

    for file in files:
        src_file = src_path / file
        dest_file = dest_path / file
        if src_file.exists():
            shutil.copy(src_file, dest_file)
            print(f"✅ Copied: {src_file} -> {dest_file}")
        else:
            print(f"⚠️ Skipped (missing): {src_file}")
            skipped.append(str(src_file))

print("\nDone. Skipped files:")
for s in skipped:
    print(" -", s)
print("\nMinimalDreamOS created at:", minimal_dir) 