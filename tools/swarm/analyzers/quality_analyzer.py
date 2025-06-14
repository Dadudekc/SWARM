"""
Quality Analyzer
---------------
Analyzes code quality metrics including complexity, duplication, and test coverage.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import re
import logging

from .base_analyzer import BaseAnalyzer, ModuleInfo, ClassInfo, FunctionInfo
from ..models.analysis import FileAnalysis

logger = logging.getLogger(__name__)

class QualityAnalyzer(BaseAnalyzer):
    """Analyzes code quality metrics including complexity and duplication."""
    
    def __init__(self, project_root: Path):
        """Initialize quality analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
        self.cyclomatic_complexity = {
            'if': 1,
            'elif': 1,
            'else': 1,
            'for': 1,
            'while': 1,
            'try': 1,
            'except': 1,
            'finally': 1,
            'with': 1,
            'assert': 1,
            'and': 1,
            'or': 1
        }
        
    def analyze_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics across the project.
        
        Returns:
            Dictionary containing quality metrics
        """
        metrics = {
            'complexity': {},
            'duplication': {},
            'coverage': {},
            'maintainability': {}
        }
        
        # Analyze all files first
        for file_path in self.project_root.rglob("*.py"):
            if not self._should_skip_file(file_path):
                module_info = self.analyze_file(file_path)
                metrics['complexity'][str(file_path)] = module_info.complexity
                metrics['duplication'][str(file_path)] = self._calculate_code_duplication(file_path)
                metrics['maintainability'][str(file_path)] = self._calculate_maintainability(module_info)
        
        # Calculate test coverage
        test_files = {str(p): self.modules[p] for p in self.project_root.rglob("test_*.py")}
        source_files = {str(p): self.modules[p] for p in self.project_root.rglob("*.py") 
                       if not str(p).endswith("test_*.py")}
        metrics['coverage'] = self.analyze_test_coverage(test_files, source_files)
        
        return metrics
        
    def _calculate_code_duplication(self, file_path: Path) -> float:
        """Calculate code duplication ratio for a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Duplication ratio between 0.0 and 1.0
        """
        try:
            with open(file_path) as f:
                source_code = f.read()
                
            # Split into lines and normalize whitespace
            lines = [line.strip() for line in source_code.split('\n')]
            lines = [line for line in lines if line and not line.startswith('#')]
            
            if not lines:
                return 0.0
                
            # Count duplicate lines
            line_counts = {}
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1
                
            # Calculate duplication ratio
            duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
            return duplicate_lines / len(lines)
            
        except Exception as e:
            logger.error(f"Error calculating duplication for {file_path}: {e}")
            return 0.0
            
    def _calculate_maintainability(self, module_info: ModuleInfo) -> float:
        """Calculate maintainability index for a module.
        
        Args:
            module_info: Module information
            
        Returns:
            Maintainability index between 0.0 and 1.0
        """
        try:
            # Calculate average complexity per function/class
            total_complexity = module_info.complexity
            total_units = len(module_info.functions) + len(module_info.classes)
            avg_complexity = total_complexity / total_units if total_units > 0 else 0
            
            # Calculate comment ratio
            total_lines = module_info.lines
            comment_lines = sum(1 for line in module_info.path.read_text().splitlines() 
                              if line.strip().startswith('#'))
            comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
            
            # Calculate dependency ratio
            total_deps = len(module_info.imports)
            dep_ratio = total_deps / total_units if total_units > 0 else 0
            
            # Weighted average of metrics
            maintainability = (
                0.4 * (1.0 - min(1.0, avg_complexity / 10.0)) +  # Complexity factor
                0.3 * min(1.0, comment_ratio * 2) +  # Documentation factor
                0.3 * (1.0 - min(1.0, dep_ratio / 5.0))  # Dependency factor
            )
            
            return max(0.0, min(1.0, maintainability))
            
        except Exception as e:
            logger.error(f"Error calculating maintainability: {e}")
            return 0.0
        
    def analyze_test_coverage(self, test_files: Dict[str, ModuleInfo], 
                            source_files: Dict[str, ModuleInfo]) -> Dict[str, float]:
        """Calculate test coverage for each source file.
        
        Args:
            test_files: Dictionary of test file analyses
            source_files: Dictionary of source file analyses
            
        Returns:
            Dictionary mapping source files to coverage ratios
        """
        coverage = {}
        
        for source_path, source_info in source_files.items():
            # Find corresponding test file
            test_path = f"tests/test_{Path(source_path).stem}.py"
            if test_path in test_files:
                test_info = test_files[test_path]
                
                # Calculate coverage based on multiple factors
                complexity_ratio = min(1.0, test_info.complexity / source_info.complexity) if source_info.complexity > 0 else 1.0
                
                # Check for test methods matching source methods
                test_methods = set(test_info.functions.keys())
                source_methods = set(source_info.functions.keys())
                method_ratio = len(test_methods & source_methods) / len(source_methods) if source_methods else 1.0
                
                # Check for test classes matching source classes
                test_classes = set(test_info.classes.keys())
                source_classes = set(source_info.classes.keys())
                class_ratio = len(test_classes & source_classes) / len(source_classes) if source_classes else 1.0
                
                # Weighted average of coverage factors
                coverage[source_path] = (
                    0.4 * complexity_ratio +
                    0.3 * method_ratio +
                    0.3 * class_ratio
                )
            else:
                coverage[source_path] = 0.0
                
        return coverage
        
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped in analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be skipped
        """
        # Skip test files
        if 'test' in file_path.name.lower():
            return True
            
        # Skip __init__.py files
        if file_path.name == '__init__.py':
            return True
            
        return False 
