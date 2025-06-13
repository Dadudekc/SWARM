"""
Dream.OS Import Analyzer

Module for analyzing and validating Python imports.
"""

import ast
import importlib
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

logger = logging.getLogger(__name__)

class ImportIssueType(Enum):
    """Types of import issues that can be detected."""
    MISSING_IMPORT = "missing_import"
    BACKSLASH_IMPORT = "backslash_import"
    INVALID_PATH = "invalid_path"
    SYNTAX_ERROR = "syntax_error"
    UNUSED_IMPORT = "unused_import"
    CIRCULAR_IMPORT = "circular_import"
    WILDCARD_IMPORT = "wildcard_import"

@dataclass
class ImportIssue:
    """Represents an issue found with imports in a file."""
    file_path: str
    issue_type: ImportIssueType
    description: str
    line_number: Optional[int] = None
    import_statement: Optional[str] = None
    severity: str = "warning"  # warning, error, info

@dataclass
class ImportAnalysis:
    """Results of import analysis for a file or project."""
    file_path: str
    issues: List[ImportIssue] = field(default_factory=list)
    imports: Dict[str, List[str]] = field(default_factory=dict)  # module -> imported names
    unused_imports: List[str] = field(default_factory=list)
    circular_imports: List[Tuple[str, str]] = field(default_factory=list)
    wildcard_imports: List[str] = field(default_factory=list)

class ImportAnalyzer:
    """Analyzes Python imports for issues and best practices."""
    
    def __init__(self, project_dir: str):
        """Initialize the import analyzer.
        
        Args:
            project_dir: Path to project directory
        """
        self.project_dir = Path(project_dir)
        self.logger = logging.getLogger(__name__)
        
    def analyze_file(self, file_path: Path) -> ImportAnalysis:
        """Analyze imports in a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            ImportAnalysis object containing analysis results
        """
        analysis = ImportAnalysis(file_path=str(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content)
            
            # Find all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name == '*':
                            analysis.wildcard_imports.append(
                                ast.get_source_segment(content, node)
                            )
                            analysis.issues.append(ImportIssue(
                                file_path=str(file_path),
                                issue_type=ImportIssueType.WILDCARD_IMPORT,
                                description="Wildcard import detected",
                                line_number=node.lineno,
                                import_statement=ast.get_source_segment(content, node),
                                severity="warning"
                            ))
                        else:
                            if name.name not in analysis.imports:
                                analysis.imports[name.name] = []
                            analysis.imports[name.name].append(name.asname or name.name)
                            
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module == '*':
                        analysis.wildcard_imports.append(
                            ast.get_source_segment(content, node)
                        )
                        analysis.issues.append(ImportIssue(
                            file_path=str(file_path),
                            issue_type=ImportIssueType.WILDCARD_IMPORT,
                            description="Wildcard import detected",
                            line_number=node.lineno,
                            import_statement=ast.get_source_segment(content, node),
                            severity="warning"
                        ))
                    else:
                        for name in node.names:
                            if name.name == '*':
                                analysis.wildcard_imports.append(
                                    ast.get_source_segment(content, node)
                                )
                                analysis.issues.append(ImportIssue(
                                    file_path=str(file_path),
                                    issue_type=ImportIssueType.WILDCARD_IMPORT,
                                    description="Wildcard import detected",
                                    line_number=node.lineno,
                                    import_statement=ast.get_source_segment(content, node),
                                    severity="warning"
                                ))
                            else:
                                if module not in analysis.imports:
                                    analysis.imports[module] = []
                                analysis.imports[module].append(name.asname or name.name)
                                
            # Check for backslash imports
            if '\\' in content and ('import' in content or 'from' in content):
                analysis.issues.append(ImportIssue(
                    file_path=str(file_path),
                    issue_type=ImportIssueType.BACKSLASH_IMPORT,
                    description="Backslash in import path detected",
                    severity="error"
                ))
                
            # Check for missing imports
            for module in analysis.imports:
                try:
                    importlib.import_module(module)
                except ImportError:
                    analysis.issues.append(ImportIssue(
                        file_path=str(file_path),
                        issue_type=ImportIssueType.MISSING_IMPORT,
                        description=f"Module '{module}' not found",
                        severity="error"
                    ))
                    
            # Check for unused imports
            # TODO: Implement unused import detection using AST analysis
            
            # Check for circular imports
            # TODO: Implement circular import detection using dependency graph
            
        except SyntaxError as e:
            analysis.issues.append(ImportIssue(
                file_path=str(file_path),
                issue_type=ImportIssueType.SYNTAX_ERROR,
                description=f"Syntax error: {str(e)}",
                line_number=e.lineno,
                severity="error"
            ))
        except Exception as e:
            analysis.issues.append(ImportIssue(
                file_path=str(file_path),
                issue_type=ImportIssueType.SYNTAX_ERROR,
                description=f"Error analyzing file: {str(e)}",
                severity="error"
            ))
            
        return analysis
        
    def analyze_project(self) -> Dict[str, ImportAnalysis]:
        """Analyze imports across the entire project.
        
        Returns:
            Dictionary mapping file paths to ImportAnalysis objects
        """
        results = {}
        
        # Find all Python files
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        results[str(file_path)] = self.analyze_file(file_path)
                    except Exception as e:
                        self.logger.error(f"Error analyzing {file_path}: {e}")
                        
        return results
        
    def generate_report(self, analysis: Dict[str, ImportAnalysis],
                       output_file: Optional[str] = None) -> str:
        """Generate a report of import analysis results.
        
        Args:
            analysis: Dictionary of ImportAnalysis objects
            output_file: Optional path to write report to
            
        Returns:
            Report as a string
        """
        report = ["=== Import Analysis Report ===\n"]
        
        # Group issues by type
        issues_by_type = {t: [] for t in ImportIssueType}
        for file_analysis in analysis.values():
            for issue in file_analysis.issues:
                issues_by_type[issue.issue_type].append(issue)
                
        # Write report sections
        for issue_type in ImportIssueType:
            issues = issues_by_type[issue_type]
            if issues:
                report.append(f"\n=== {issue_type.value.title()} ===\n")
                for issue in issues:
                    report.append(f"\n{issue.file_path}")
                    if issue.line_number:
                        report.append(f" (line {issue.line_number})")
                    report.append(f":\n  {issue.description}")
                    if issue.import_statement:
                        report.append(f"\n  Import: {issue.import_statement}")
                    report.append(f"\n  Severity: {issue.severity}")
                    report.append("\n")
                    
        # Write summary
        total_issues = sum(len(issues) for issues in issues_by_type.values())
        report.append("\n=== Summary ===\n")
        report.append(f"Total files analyzed: {len(analysis)}")
        report.append(f"Total issues found: {total_issues}")
        for issue_type in ImportIssueType:
            issues = issues_by_type[issue_type]
            if issues:
                report.append(f"{issue_type.value}: {len(issues)}")
                
        report_str = "\n".join(report)
        
        # Write to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_str)
            self.logger.info(f"Report written to {output_file}")
            
        return report_str 