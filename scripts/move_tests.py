"""
Script to move test files from old locations to new ones.
"""

import os
import shutil
from pathlib import Path

def move_test_files():
    """Move test files from old locations to new ones."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    old_social_dir = base_dir / "tests" / "social"
    old_stubborn_dir = base_dir / "tests" / "stubborn"
    new_social_dir = base_dir / "tests" / "core" / "social"
    new_stubborn_dir = base_dir / "tests" / "core" / "stubborn"
    
    # Create new directories if they don't exist
    new_social_dir.mkdir(parents=True, exist_ok=True)
    new_stubborn_dir.mkdir(parents=True, exist_ok=True)
    
    # Move social test files
    if old_social_dir.exists():
        for file in old_social_dir.glob("**/*.py"):
            if file.name != "__init__.py":
                new_path = new_social_dir / file.name
                shutil.move(str(file), str(new_path))
                print(f"Moved {file} to {new_path}")
    
    # Move stubborn test files
    if old_stubborn_dir.exists():
        for file in old_stubborn_dir.glob("**/*.py"):
            if file.name != "__init__.py":
                new_path = new_stubborn_dir / file.name
                shutil.move(str(file), str(new_path))
                print(f"Moved {file} to {new_path}")
    
    # Remove old directories if they're empty
    if old_social_dir.exists() and not any(old_social_dir.iterdir()):
        old_social_dir.rmdir()
        print(f"Removed empty directory: {old_social_dir}")
    
    if old_stubborn_dir.exists() and not any(old_stubborn_dir.iterdir()):
        old_stubborn_dir.rmdir()
        print(f"Removed empty directory: {old_stubborn_dir}")

if __name__ == "__main__":
    move_test_files() 