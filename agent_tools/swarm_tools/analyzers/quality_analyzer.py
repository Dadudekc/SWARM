import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from ..models.analysis import FileAnalysis

class QualityAnalyzer:
    """Analyzes code quality metrics including complexity and duplication."""
    
    def __init__(self):
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
        
    def analyze_file_quality(self, file_path: Path, source_code: str) -> Tuple[int, int]:
        """Analyze cyclomatic complexity and code duplication for a file."""
        try:
            tree = ast.parse(source_code)
            complexity = self._calculate_cyclomatic_complexity(tree)
            duplication = self._calculate_code_duplication(source_code)
            return complexity, duplication
        except Exception as e:
            print(f"Error analyzing quality metrics in {file_path}: {e}")
            return 0, 0
            
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                complexity += 1
            elif isinstance(node, ast.For):
                complexity += 1
            elif isinstance(node, ast.While):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                if isinstance(node.op, (ast.And, ast.Or)):
                    complexity += 1
                    
        return complexity
        
    def _calculate_code_duplication(self, source_code: str) -> int:
        """Calculate number of duplicate lines in the code."""
        # Split into lines and normalize whitespace
        lines = [line.strip() for line in source_code.split('\n')]
        lines = [line for line in lines if line and not line.startswith('#')]
        
        # Count duplicate lines
        line_counts = {}
        for line in lines:
            line_counts[line] = line_counts.get(line, 0) + 1
            
        # Sum up duplicate lines (count > 1)
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        
        return duplicate_lines
        
    def analyze_test_coverage(self, test_files: Dict[str, FileAnalysis], 
                            source_files: Dict[str, FileAnalysis]) -> Dict[str, float]:
        """Calculate test coverage for each source file."""
        coverage = {}
        
        for source_path, source_analysis in source_files.items():
            # Find corresponding test file
            test_path = f"tests/test_{Path(source_path).stem}.py"
            if test_path in test_files:
                # Calculate coverage based on test file complexity vs source file complexity
                test_complexity = test_files[test_path].complexity
                source_complexity = source_analysis.complexity
                if source_complexity > 0:
                    coverage[source_path] = min(1.0, test_complexity / source_complexity)
                else:
                    coverage[source_path] = 1.0
            else:
                coverage[source_path] = 0.0
                
        return coverage 