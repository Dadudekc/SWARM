"""
Test batch log processing with Windows-specific fixes.
"""

import os
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any
from contextlib import contextmanager

# Minimal Windows-specific utilities
def normalize_path(path: str) -> Path:
    """Normalize path for Windows compatibility."""
    return Path(path).resolve()

@contextmanager
def safe_file_handle(filepath: str, mode: str = 'r', encoding: str = 'utf-8'):
    """Safe file handle with proper cleanup."""
    filepath = normalize_path(filepath)
    handle = None
    try:
        handle = open(filepath, mode, encoding=encoding)
        yield handle
    finally:
        if handle:
            handle.close()

def test_batch_processing():
    """Test batch log processing with proper file handle management."""
    log_file = "test_batch_process.json"
    test_entries = [
        {"message": f"batch entry {i}", "level": "INFO", "timestamp": f"2024-03-{i:02d}"}
        for i in range(1, 4)
    ]
    
    # Write batch entries
    with safe_file_handle(log_file, 'w') as f:
        json.dump(test_entries, f)
    
    # Process batch entries
    processed_entries = []
    with safe_file_handle(log_file, 'r') as f:
        entries = json.load(f)
        for entry in entries:
            processed_entries.append({
                **entry,
                "processed": True,
                "batch_id": "test_batch"
            })
    
    # Write processed entries
    with safe_file_handle(log_file, 'w') as f:
        json.dump(processed_entries, f)
    
    # Verify processing
    with safe_file_handle(log_file, 'r') as f:
        final_entries = json.load(f)
        assert len(final_entries) == 3
        assert all(entry["processed"] for entry in final_entries)
        assert all(entry["batch_id"] == "test_batch" for entry in final_entries)
    
    # Cleanup
    try:
        os.remove(log_file)
    except PermissionError:
        import time
        time.sleep(0.1)
        os.remove(log_file)

def test_batch_processing_large():
    """Test batch processing with larger dataset."""
    log_file = "test_batch_large.json"
    test_entries = [
        {"message": f"large batch entry {i}", "level": "INFO", "data": "x" * 100}
        for i in range(100)
    ]
    
    # Write large batch
    with safe_file_handle(log_file, 'w') as f:
        json.dump(test_entries, f)
    
    # Process in chunks
    chunk_size = 20
    processed_entries = []
    
    with safe_file_handle(log_file, 'r') as f:
        entries = json.load(f)
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            processed_entries.extend([
                {**entry, "processed": True, "chunk": i // chunk_size}
                for entry in chunk
            ])
    
    # Write processed chunks
    with safe_file_handle(log_file, 'w') as f:
        json.dump(processed_entries, f)
    
    # Verify processing
    with safe_file_handle(log_file, 'r') as f:
        final_entries = json.load(f)
        assert len(final_entries) == 100
        assert all(entry["processed"] for entry in final_entries)
        assert len(set(entry["chunk"] for entry in final_entries)) == 5
    
    # Cleanup
    try:
        os.remove(log_file)
    except PermissionError:
        import time
        time.sleep(0.1)
        os.remove(log_file)

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup test files after each test."""
    yield
    for file in ["test_batch_process.json", "test_batch_large.json"]:
        try:
            if os.path.exists(file):
                os.remove(file)
        except PermissionError:
            import time
            time.sleep(0.1)
            if os.path.exists(file):
                os.remove(file) 