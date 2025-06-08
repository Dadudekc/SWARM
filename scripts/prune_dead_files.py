#!/usr/bin/env python3
"""
Test file pruning tool for Dream.OS.
Identifies and optionally removes dead test files based on:
- No corresponding implementation
- Empty test files
- Duplicate test files
- Unused fixtures
"""

import os
import sys
import json
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import ast
import argparse
from collections import defaultdict

class TestPruner:
    def __init__(
        self,
        dry_run: bool = True,
        mode: str = "analyze",
        output_dir: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        keeplist_path: Optional[Path] = None
    ):
        self.root_dir = Path(__file__).parent.parent
        self.tests_dir = self.root_dir / "tests"
        self.src_dir = self.root_dir / "dreamos"
        self.dry_run = dry_run
        self.mode = mode
        self.output_dir = output_dir or (self.tests_dir / "report")
        self.backup_dir = backup_dir or (self.tests_dir / "_archive")
        self.keeplist_path = keeplist_path or (self.tests_dir / "test_keeplist.yaml")
        
        # Track files and their status
        self.dead_files: List[Path] = []
        self.empty_files: List[Path] = []
        self.duplicate_files: List[Tuple[Path, Path]] = []
        self.unused_fixtures: List[Path] = []
        self.critical_files: List[Path] = []
        
        # Load keeplist if exists
        self.keeplist: Dict[str, bool] = {}
        if self.keeplist_path.exists():
            with open(self.keeplist_path, "r") as f:
                self.keeplist = yaml.safe_load(f) or {}
        
        # Cache for implementation files
        self.impl_files: Dict[str, Path] = {}
        self._build_impl_cache()

    def _build_impl_cache(self):
        """Build cache of implementation files."""
        for path in self.src_dir.rglob("*.py"):
            if path.name != "__init__.py":
                # Store both with and without 'test_' prefix
                self.impl_files[path.stem] = path
                self.impl_files[f"test_{path.stem}"] = path

    def _is_empty_test(self, file_path: Path) -> bool:
        """Check if a test file is empty or has no actual tests."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if not content.strip():
                return True
                
            # Parse AST to check for test functions
            tree = ast.parse(content)
            has_tests = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        has_tests = True
                        break
            
            return not has_tests
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")
            return False

    def _is_critical_test(self, file_path: Path) -> bool:
        """Determine if a test file is critical based on various factors."""
        # Check keeplist first
        rel_path = str(file_path.relative_to(self.root_dir))
        if rel_path in self.keeplist:
            return self.keeplist[rel_path]
        
        # Check file content for critical markers
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Look for critical markers in content
            critical_markers = [
                "@pytest.mark.critical",
                "# critical test",
                "# core functionality",
                "# required for"
            ]
            
            if any(marker in content.lower() for marker in critical_markers):
                return True
                
            # Check if it's in a critical directory
            critical_dirs = {
                "core", "messaging", "autonomy", "bridge",
                "security", "utils", "cli"
            }
            
            path_parts = str(file_path).lower().split(os.sep)
            return any(crit_dir in path_parts for crit_dir in critical_dirs)
            
        except Exception as e:
            print(f"⚠️ Error checking critical status of {file_path}: {e}")
            return False

    def _find_duplicates(self):
        """Find duplicate test files based on content hash."""
        content_hashes: Dict[str, List[Path]] = defaultdict(list)
        
        for path in self.tests_dir.rglob("test_*.py"):
            if path.name == "__init__.py":
                continue
                
            try:
                with open(path, "rb") as f:
                    content = f.read()
                    # Simple hash of content
                    content_hash = hash(content)
                    content_hashes[content_hash].append(path)
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")
        
        # Find duplicates
        for paths in content_hashes.values():
            if len(paths) > 1:
                self.duplicate_files.extend(
                    (p1, p2) for i, p1 in enumerate(paths) for p2 in paths[i+1:]
                )

    def _check_fixtures(self):
        """Check for unused fixtures."""
        fixture_dir = self.tests_dir / "fixtures"
        if not fixture_dir.exists():
            return
            
        # Get all fixture files
        fixture_files = set(fixture_dir.rglob("*.py"))
        used_fixtures = set()
        
        # Check all test files for fixture usage
        for path in self.tests_dir.rglob("test_*.py"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Look for fixture imports
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if "fixtures" in node.module:
                            for name in node.names:
                                used_fixtures.add(name.name)
            except Exception as e:
                print(f"⚠️ Error checking fixtures in {path}: {e}")
        
        # Find unused fixtures
        for path in fixture_files:
            if path.stem not in used_fixtures:
                self.unused_fixtures.append(path)

    def analyze(self):
        """Analyze test files for issues."""
        print("🔍 Analyzing test files...")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for dead files and critical tests
        for path in self.tests_dir.rglob("test_*.py"):
            if path.name == "__init__.py":
                continue
                
            # Check if implementation exists
            impl_name = path.stem[5:] if path.stem.startswith("test_") else path.stem
            if impl_name not in self.impl_files:
                if not self._is_critical_test(path):
                    self.dead_files.append(path)
                else:
                    self.critical_files.append(path)
            
            # Check if file is empty
            if self._is_empty_test(path):
                self.empty_files.append(path)
        
        # Find duplicates
        self._find_duplicates()
        
        # Check fixtures
        self._check_fixtures()
        
        # Save analysis results
        self._save_analysis()
        
        # Print summary
        self._print_summary()

    def _save_analysis(self):
        """Save analysis results to JSON files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save critical tests
        critical_data = {
            "timestamp": timestamp,
            "critical_files": [
                {
                    "path": str(p.relative_to(self.root_dir)),
                    "reason": "marked as critical",
                    "preserve": True
                }
                for p in self.critical_files
            ]
        }
        
        with open(self.output_dir / f"critical_tests_{timestamp}.json", "w") as f:
            json.dump(critical_data, f, indent=2)
        
        # Save prune log
        prune_data = {
            "timestamp": timestamp,
            "dead_files": [str(p.relative_to(self.root_dir)) for p in self.dead_files],
            "empty_files": [str(p.relative_to(self.root_dir)) for p in self.empty_files],
            "duplicate_files": [
                {
                    "original": str(p1.relative_to(self.root_dir)),
                    "duplicate": str(p2.relative_to(self.root_dir))
                }
                for p1, p2 in self.duplicate_files
            ],
            "unused_fixtures": [str(p.relative_to(self.root_dir)) for p in self.unused_fixtures]
        }
        
        with open(self.output_dir / f"prune_log_{timestamp}.json", "w") as f:
            json.dump(prune_data, f, indent=2)

    def _print_summary(self):
        """Print analysis summary."""
        print("\n📊 Analysis Summary:")
        
        if self.critical_files:
            print("\n🔒 Critical Test Files (preserved):")
            for path in self.critical_files:
                print(f"  - {path.relative_to(self.root_dir)}")
        
        if self.dead_files:
            print("\n❌ Dead Test Files (no implementation):")
            for path in self.dead_files:
                print(f"  - {path.relative_to(self.root_dir)}")
        
        if self.empty_files:
            print("\n⚠️ Empty Test Files:")
            for path in self.empty_files:
                print(f"  - {path.relative_to(self.root_dir)}")
        
        if self.duplicate_files:
            print("\n🔄 Duplicate Test Files:")
            for p1, p2 in self.duplicate_files:
                print(f"  - {p1.relative_to(self.root_dir)}")
                print(f"    duplicates {p2.relative_to(self.root_dir)}")
        
        if self.unused_fixtures:
            print("\n🗑️ Unused Fixtures:")
            for path in self.unused_fixtures:
                print(f"  - {path.relative_to(self.root_dir)}")

    def cleanup(self):
        """Clean up identified issues."""
        if self.dry_run:
            print("\n🔒 Dry run - no files will be modified")
            return
            
        print("\n🧹 Cleaning up...")
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Move files to backup instead of deleting
        for path in self.dead_files + self.empty_files + [p2 for _, p2 in self.duplicate_files] + self.unused_fixtures:
            try:
                rel_path = path.relative_to(self.tests_dir)
                backup_file = backup_path / rel_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(backup_file))
                print(f"✅ Moved to backup: {rel_path}")
            except Exception as e:
                print(f"❌ Error moving {path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Prune dead test files")
    parser.add_argument(
        "--mode",
        choices=["analyze", "cleanup"],
        default="analyze",
        help="Operation mode"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually remove files (default is dry run)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for analysis output"
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Directory for file backups"
    )
    parser.add_argument(
        "--keeplist",
        type=Path,
        help="Path to test keeplist YAML"
    )
    
    args = parser.parse_args()
    
    pruner = TestPruner(
        dry_run=not args.execute,
        mode=args.mode,
        output_dir=args.output_dir,
        backup_dir=args.backup_dir,
        keeplist_path=args.keeplist
    )
    
    pruner.analyze()
    
    if args.mode == "cleanup" and args.execute:
        pruner.cleanup()
    elif args.mode == "analyze":
        print("\n💡 Run with --mode cleanup --execute to move files to backup")
        print("💡 Check the report directory for detailed analysis")

if __name__ == "__main__":
    main() 