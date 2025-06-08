#!/usr/bin/env python3
"""
Reorganize test files to match module structure.
Ensures consistent naming and proper test organization.
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast
from datetime import datetime

class TestReorganizer:
    def __init__(self, source_dir: str, test_dir: str, dry_run: bool = False):
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.dry_run = dry_run
        self.actions = []
        self.log_file = "reorg_log.json"
        
    def find_source_modules(self) -> Dict[str, Path]:
        """Find all Python modules in source directory."""
        modules = {}
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.source_dir)
                    module_name = str(rel_path).replace(os.sep, '.').replace('.py', '')
                    modules[module_name] = full_path
        return modules
    
    def find_test_files(self) -> Dict[str, Path]:
        """Find all test files in test directory."""
        tests = {}
        for root, _, files in os.walk(self.test_dir):
            for file in files:
                # Skip bytecode files and __init__.py
                if file.endswith('.pyc') or file == '__init__.py':
                    continue
                if file.endswith('_test.py') or file.startswith('test_'):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.test_dir)
                    test_name = str(rel_path).replace(os.sep, '.').replace('.py', '')
                    tests[test_name] = full_path
        return tests
    
    def get_module_from_test(self, test_path: Path) -> str:
        """Extract module name from test file content."""
        try:
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read().replace('\r\n', '\n')  # Normalize line endings
                tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'dreamos' in node.module:
                        return node.module.replace('dreamos.', '')
        except Exception as e:
            print(f"Error parsing {test_path}: {e}")
        return None
    
    def get_target_path(self, module_name: str) -> Path:
        """Get target path for test file based on module name."""
        parts = module_name.split('.')
        test_name = f"test_{parts[-1]}.py"
        return self.test_dir / os.sep.join(parts[:-1]) / test_name
    
    def ensure_init_files(self, path: Path) -> None:
        """Ensure __init__.py exists in all directories up to path."""
        current = path.parent
        while current != self.test_dir:
            init_file = current / "__init__.py"
            if not init_file.exists():
                if not self.dry_run:
                    init_file.touch()
                self.actions.append({
                    "action": "create_init",
                    "path": str(init_file),
                    "timestamp": datetime.now().isoformat()
                })
            current = current.parent
    
    def create_readme(self, path: Path) -> None:
        """Create README.md for test directory."""
        readme_path = path / "README.md"
        if not readme_path.exists():
            content = f"""# Tests for {path.relative_to(self.test_dir)}

This directory contains tests for the corresponding module in `{self.source_dir}`.

## Structure

- `test_*.py`: Individual test files
- `conftest.py`: Shared fixtures
- `__init__.py`: Package marker

## Running Tests

```bash
pytest {path.relative_to(self.test_dir)}
```
"""
            if not self.dry_run:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            self.actions.append({
                "action": "create_readme",
                "path": str(readme_path),
                "timestamp": datetime.now().isoformat()
            })
    
    def move_test_file(self, source: Path, target: Path) -> None:
        """Move test file to target location."""
        if source != target:
            if not self.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
            self.actions.append({
                "action": "move_file",
                "source": str(source),
                "target": str(target),
                "timestamp": datetime.now().isoformat()
            })
    
    def reorganize(self) -> None:
        """Main reorganization logic."""
        modules = self.find_source_modules()
        tests = self.find_test_files()
        
        for test_name, test_path in tests.items():
            module_name = self.get_module_from_test(test_path)
            if module_name:
                target_path = self.get_target_path(module_name)
                self.ensure_init_files(target_path)
                self.move_test_file(test_path, target_path)
                self.create_readme(target_path.parent)
        
        # Log actions
        if not self.dry_run:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.actions, f, indent=2)
        
        # Print summary
        print(f"\n📊 Reorganization Summary:")
        print(f"📁 Source Directory: {self.source_dir}")
        print(f"🧪 Test Directory: {self.test_dir}")
        print(f"📝 Actions Log: {self.log_file}")
        print(f"🔍 {'Dry Run' if self.dry_run else 'Executed'}")
        print(f"📋 Total Actions: {len(self.actions)}")

def main():
    parser = argparse.ArgumentParser(description="Reorganize test files to match module structure")
    parser.add_argument("--source", default="dreamos", help="Source directory containing modules")
    parser.add_argument("--tests", default="tests", help="Test directory to reorganize")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    reorganizer = TestReorganizer(args.source, args.tests, args.dry_run)
    reorganizer.reorganize()

if __name__ == "__main__":
    main() 