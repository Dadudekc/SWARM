"""
Cleanup script to remove test artifacts from the project root.
"""

import os
import shutil
from pathlib import Path

def cleanup_test_artifacts():
    """Remove test artifacts from the project root."""
    project_root = Path(__file__).parent.parent
    
    # List of directories to check and remove
    test_dirs = [
        "test_runtime",
        "test_logs",
        "test_config",
        "test_data",
        "test_output",
        "test_voice_queue",
        "temp_test_dir",
        "test_audio",
        "logs",
        "runtime"
    ]
    
    # List of files to check and remove
    test_files = [
        "test_config.json",
        "test_config.yaml",
        "agent_config.yaml",
        "social_config.json"
    ]
    
    # Remove directories
    for dir_name in test_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"Removing directory: {dir_path}")
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"Error removing {dir_path}: {e}")
    
    # Remove files
    for file_name in test_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"Removing file: {file_path}")
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    cleanup_test_artifacts() 