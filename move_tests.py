"""
Script to move all test files to the main tests directory.
"""

import os
import shutil
from pathlib import Path

def find_test_files(start_dir):
    """Find all test files recursively."""
    test_files = []
    for root, _, files in os.walk(start_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return test_files

def get_target_path(source_path):
    """Get the target path for a test file."""
    # Convert to Path object for easier manipulation
    source_path = Path(source_path)
    
    # Get the relative path from dreamos
    if 'dreamos' in source_path.parts:
        idx = source_path.parts.index('dreamos')
        rel_path = source_path.parts[idx+1:]
    else:
        rel_path = source_path.parts
    
    # Create target path
    target_path = Path('tests') / Path(*rel_path)
    
    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    return target_path

def move_test_files():
    """Move all test files to the main tests directory."""
    # Find all test files
    test_files = find_test_files('dreamos')
    
    # Move each test file
    for source_path in test_files:
        target_path = get_target_path(source_path)
        print(f"Moving {source_path} to {target_path}")
        
        # Read source file
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Write to target file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Delete source file
        os.remove(source_path)

if __name__ == '__main__':
    move_test_files() 