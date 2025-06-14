"""
Analysis Models
--------------
Data models for code analysis results.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import datetime

@dataclass
class ClassInfo:
    """Information about a class in the codebase."""
    name: str
    methods: List[str]
    docstring: Optional[str]
    base_classes: List[str]
    maturity: str
    agent_type: str
    complexity: int
    dependencies: Set[str]

    def to_dict(self) -> dict:
        """Convert class info to dictionary format for JSON serialization."""
        return {
            "name": self.name,
            "methods": self.methods,
            "docstring": self.docstring,
            "base_classes": self.base_classes,
            "maturity": self.maturity,
            "agent_type": self.agent_type,
            "complexity": self.complexity,
            "dependencies": list(self.dependencies)
        }

@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    path: Path
    imports: Set[str] = field(default_factory=set)
    functions: Dict[str, dict] = field(default_factory=dict)
    classes: Dict[str, dict] = field(default_factory=dict)
    complexity: int = 0
    lines: int = 0
    dependencies: Set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        """Convert analysis to dictionary format for JSON serialization."""
        return {
            "path": str(self.path),
            "imports": list(self.imports),
            "functions": self.functions,
            "classes": self.classes,
            "complexity": self.complexity,
            "lines": self.lines,
            "dependencies": list(self.dependencies)
        }

@dataclass
class ProjectAnalysis:
    """Analysis results for an entire project."""
    root: Path
    files: Dict[str, FileAnalysis] = field(default_factory=dict)
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_complexity: int = 0
    total_lines: int = 0
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert analysis to dictionary format for JSON serialization."""
        return {
            "root": str(self.root),
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "total_files": self.total_files,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "total_imports": self.total_imports,
            "total_complexity": self.total_complexity,
            "total_lines": self.total_lines,
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "circular_dependencies": self.circular_dependencies
        } 
