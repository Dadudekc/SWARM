"""
File Metrics Utility
------------------
Unified tool for analyzing file sizes, module metrics, and code statistics.
Provides both CLI and programmatic interfaces for file analysis.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Generator
import argparse
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: Path
    lines: int
    size_bytes: int
    last_modified: datetime
    is_python: bool
    imports: List[str] = None
    classes: List[str] = None
    functions: List[str] = None

class FileMetricsAnalyzer:
    """Analyzes file metrics across a codebase."""
    
    def __init__(
        self,
        threshold: int = 300,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None
    ):
        """Initialize analyzer.
        
        Args:
            threshold: Default line count threshold for large files
            exclude_patterns: Glob patterns to exclude
            include_patterns: Glob patterns to include (if None, include all)
        """
        self.threshold = threshold
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or ["*.py"]
        
    def _should_analyze(self, path: Path) -> bool:
        """Check if file should be analyzed.
        
        Args:
            path: File path to check
            
        Returns:
            bool: True if file should be analyzed
        """
        # Skip excluded patterns
        if any(path.match(pattern) for pattern in self.exclude_patterns):
            return False
            
        # Check include patterns
        if not any(path.match(pattern) for pattern in self.include_patterns):
            return False
            
        # Skip special files
        if path.name.startswith("__"):
            return False
            
        # Skip hidden directories
        if any(part.startswith(".") for part in path.parts):
            return False
            
        return True
        
    def analyze_file(self, path: Path) -> Optional[FileMetrics]:
        """Analyze metrics for a single file.
        
        Args:
            path: Path to file
            
        Returns:
            FileMetrics if file should be analyzed, None otherwise
        """
        if not self._should_analyze(path):
            return None
            
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n")
            size_bytes = path.stat().st_size
            last_modified = datetime.fromtimestamp(path.stat().st_mtime)
            is_python = path.suffix == ".py"
            
            metrics = FileMetrics(
                path=path,
                lines=lines,
                size_bytes=size_bytes,
                last_modified=last_modified,
                is_python=is_python
            )
            
            # Additional Python-specific analysis
            if is_python:
                metrics.imports = self._extract_imports(content)
                metrics.classes = self._extract_classes(content)
                metrics.functions = self._extract_functions(content)
                
            return metrics
            
        except Exception as e:
            print(f"[!] Error analyzing {path}: {e}", file=sys.stderr)
            return None
            
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code.
        
        Args:
            content: File content
            
        Returns:
            List of import statements
        """
        imports = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith(("import ", "from ")):
                imports.append(line)
        return imports
        
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class definitions from Python code.
        
        Args:
            content: File content
            
        Returns:
            List of class names
        """
        classes = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("class "):
                class_name = line[6:].split("(")[0].strip()
                classes.append(class_name)
        return classes
        
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function definitions from Python code.
        
        Args:
            content: File content
            
        Returns:
            List of function names
        """
        functions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("def "):
                func_name = line[4:].split("(")[0].strip()
                functions.append(func_name)
        return functions
        
    def find_large_files(
        self,
        root: Path,
        threshold: Optional[int] = None
    ) -> Generator[Tuple[Path, int], None, None]:
        """Find files exceeding size threshold.
        
        Args:
            root: Root directory to scan
            threshold: Line count threshold (uses default if None)
            
        Yields:
            (path, line_count) tuples for large files
        """
        threshold = threshold or self.threshold
        
        for path in root.rglob("*"):
            if not path.is_file():
                continue
                
            metrics = self.analyze_file(path)
            if metrics and metrics.lines > threshold:
                yield path, metrics.lines
                
    def analyze_module_sizes(
        self,
        base: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze module sizes with detailed metrics.
        
        Args:
            base: Base directory to scan
            limit: Maximum lines allowed (uses default if None)
            
        Returns:
            Dictionary containing analysis results
        """
        limit = limit or self.threshold
        oversized = []
        total_files = 0
        total_lines = 0
        total_size = 0
        
        for path in Path(base).rglob("*"):
            if not path.is_file():
                continue
                
            metrics = self.analyze_file(path)
            if not metrics:
                continue
                
            total_files += 1
            total_lines += metrics.lines
            total_size += metrics.size_bytes
            
            if metrics.lines > limit:
                oversized.append({
                    "path": str(metrics.path),
                    "lines": metrics.lines,
                    "size_bytes": metrics.size_bytes,
                    "last_modified": metrics.last_modified.isoformat(),
                    "imports": metrics.imports,
                    "classes": metrics.classes,
                    "functions": metrics.functions
                })
                
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_size_bytes": total_size,
            "oversized_modules": sorted(oversized, key=lambda x: x["lines"], reverse=True)
        }

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Analyze file metrics")
    parser.add_argument(
        "--base",
        default=".",
        help="Base directory to scan"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=300,
        help="Maximum lines of code allowed"
    )
    parser.add_argument(
        "--fail-on-hit",
        action="store_true",
        help="Exit with error if oversized modules found"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Glob patterns to exclude"
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=["*.py"],
        help="Glob patterns to include"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    args = parser.parse_args()
    
    analyzer = FileMetricsAnalyzer(
        threshold=args.threshold,
        exclude_patterns=args.exclude,
        include_patterns=args.include
    )
    
    # Analyze files
    results = analyzer.analyze_module_sizes(args.base)
    
    # Report results
    if args.format == "json":
        import json
        print(json.dumps(results, indent=2))
    else:
        print(f"\nAnalyzed {results['total_files']} files:")
        print(f"Total lines: {results['total_lines']}")
        print(f"Total size: {results['total_size_bytes'] / 1024:.1f} KB")
        
        if results["oversized_modules"]:
            print(f"\n[!] Found {len(results['oversized_modules'])} oversized modules:")
            for module in results["oversized_modules"]:
                print(f"\n  - {module['path']} ({module['lines']} LOC)")
                if module["classes"]:
                    print(f"    Classes: {', '.join(module['classes'])}")
                if module["functions"]:
                    print(f"    Functions: {', '.join(module['functions'])}")
                    
            if args.fail_on_hit:
                sys.exit(1)
        else:
            print("\n[✓] No oversized modules found")

if __name__ == "__main__":
    main() 