"""
Release Preparation Script
-------------------------
Prepares a release bundle for the logging system integration.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def generate_changelog():
    """Generate CHANGELOG.md from .gitmessage."""
    with open(".gitmessage", "r") as f:
        content = f.read()
    
    # Extract version and date
    version = "1.0.0"  # You might want to get this from somewhere
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Format changelog
    changelog = f"""# Changelog

## [{version}] - {date}

{content}
"""
    
    return changelog

def prepare_release():
    """Prepare the release bundle."""
    # Create release directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    release_dir = Path(f"releases/logging_integration_{timestamp}")
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy core files
    core_files = [
        "discord_bot/commands.py",
        "dreamos/core/devlog.py",
        "social/core/dispatcher.py",
        "gui/components/log_monitor.py",
        "gui/main_window.py",
        "gui/__main__.py",
        "gui/requirements.txt",
        "tests/core/test_log_manager.py",
        ".gitmessage",
        "requirements.txt"
    ]
    
    for file in core_files:
        src = Path(file)
        if src.exists():
            dst = release_dir / src
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    
    # Copy documentation
    docs_dir = release_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    shutil.copy2("docs/logging/README.md", docs_dir / "README.md")
    
    # Generate and write CHANGELOG.md
    changelog = generate_changelog()
    with open(release_dir / "CHANGELOG.md", "w") as f:
        f.write(changelog)
    
    # Create ZIP archive
    zip_name = f"logging_integration_{timestamp}.zip"
    shutil.make_archive(
        str(release_dir),
        'zip',
        release_dir
    )
    
    # Clean up release directory
    shutil.rmtree(release_dir)
    
    print(f"Release bundle created: {zip_name}")
    print("\nContents:")
    for file in core_files:
        print(f"- {file}")
    print("- docs/README.md")
    print("- CHANGELOG.md")

if __name__ == "__main__":
    prepare_release() 
