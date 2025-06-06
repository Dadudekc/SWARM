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
    language: str
    functions: List[str]
    classes: Dict[str, ClassInfo]
    routes: List[str]
    complexity: int
    dependencies: Set[str]
    imports: Set[str]
    test_coverage: float
    cyclomatic_complexity: int
    duplicate_lines: int

    def to_dict(self) -> dict:
        """Convert analysis to dictionary format for JSON serialization."""
        return {
            "path": str(self.path),
            "language": self.language,
            "functions": self.functions,
            "classes": {name: asdict(cls) for name, cls in self.classes.items()},
            "routes": self.routes,
            "complexity": self.complexity,
            "dependencies": list(self.dependencies),
            "imports": list(self.imports),
            "test_coverage": self.test_coverage,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "duplicate_lines": self.duplicate_lines
        }

@dataclass
class ProjectAnalysis:
    """Complete project analysis results."""
    project_root: Path
    scan_time: datetime.datetime
    files: Dict[str, FileAnalysis]
    dependencies: Dict[str, Set[str]]
    circular_dependencies: List[List[str]]
    modules: Dict[str, Set[str]]
    core_components: Set[str]
    peripheral_components: Set[str]
    test_files: Dict[str, FileAnalysis]
    total_complexity: int
    total_duplication: int
    average_test_coverage: float
    errors: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert analysis to dictionary format for JSON serialization."""
        return {
            "project_root": str(self.project_root),
            "scan_time": self.scan_time.isoformat(),
            "files": {k: v.to_dict() for k, v in self.files.items()},
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "circular_dependencies": self.circular_dependencies,
            "modules": {k: list(v) for k, v in self.modules.items()},
            "core_components": list(self.core_components),
            "peripheral_components": list(self.peripheral_components),
            "test_files": {k: v.to_dict() for k, v in self.test_files.items()},
            "total_complexity": self.total_complexity,
            "total_duplication": self.total_duplication,
            "average_test_coverage": self.average_test_coverage,
            "errors": self.errors,
            "skipped_files": self.skipped_files
        } 