import os
from collections import defaultdict
from pathlib import Path

def find_duplicates_and_empty_dirs():
    test_dir = Path('tests')
    
    # Find all test files
    test_files = list(test_dir.rglob('test_*.py'))
    
    # Group by filename
    by_name = defaultdict(list)
    for f in test_files:
        by_name[f.name].append(f)
    
    # Print duplicates
    print("\n=== Duplicate Test Files ===")
    for name, files in by_name.items():
        if len(files) > 1:
            print(f"\n{name}:")
            for f in files:
                print(f"  - {f}")
    
    # Find empty directories
    print("\n=== Empty Directories ===")
    for root, dirs, files in os.walk(test_dir):
        if not dirs and not files and root != str(test_dir):
            print(f"  - {root}")

if __name__ == '__main__':
    find_duplicates_and_empty_dirs() 