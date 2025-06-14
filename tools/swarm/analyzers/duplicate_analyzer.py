"""
Duplicate Analyzer
-----------------
Analyzes code duplication and similar patterns using AST analysis.
Provides comprehensive duplicate detection for functions, classes, and code blocks.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import logging
from difflib import SequenceMatcher
import ast
from collections import defaultdict

from .base_analyzer import BaseAnalyzer, ModuleInfo, ClassInfo, FunctionInfo

logger = logging.getLogger(__name__)

class ClassVisitor(ast.NodeVisitor):
    """AST visitor for finding class definitions."""
    
    def __init__(self):
        """Initialize visitor."""
        self.classes = {}  # name -> (file, line, bases, methods)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition.
        
        Args:
            node: Class definition node
        """
        # Get base classes
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        
        # Get method names and their complexities
        methods = []
        method_complexities = {}
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                method_complexities[item.name] = self._calculate_node_complexity(item)
        
        # Store class info
        self.classes[node.name] = {
            "bases": bases,
            "methods": methods,
            "method_complexities": method_complexities,
            "complexity": self._calculate_node_complexity(node)
        }
        
        # Visit children
        self.generic_visit(node)
        
    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try,
                                ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
        return complexity

class DuplicateAnalyzer(BaseAnalyzer):
    """Analyzes code duplication using AST analysis."""
    
    def __init__(self, project_root: Path):
        """Initialize duplicate analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
        self.min_similarity = 0.8
        self.min_lines = 5
        self.class_locations = defaultdict(list)  # name -> [(file, line, info), ...]
        
    def analyze_duplicates(self, min_similarity: float = 0.8, min_lines: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze code duplication across the project.
        
        Args:
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            min_lines: Minimum number of lines to consider for duplication
            
        Returns:
            Dictionary containing different types of duplicates
        """
        self.min_similarity = min_similarity
        self.min_lines = min_lines
        
        results = {
            'functions': [],
            'classes': [],
            'blocks': [],
            'class_definitions': []
        }
        
        # Analyze all files first
        for file_path in self.project_root.rglob("*.py"):
            if not self._should_skip_file(file_path):
                self.analyze_file(file_path)
                self._analyze_class_definitions(file_path)
        
        # Find duplicates between functions
        results['functions'] = self._find_duplicate_functions()
        
        # Find duplicates between classes
        results['classes'] = self._find_duplicate_classes()
        
        # Find duplicate code blocks
        results['blocks'] = self._find_duplicate_blocks()
        
        # Find duplicate class definitions
        results['class_definitions'] = self._find_duplicate_class_definitions()
        
        return results
    
    def _analyze_class_definitions(self, file_path: Path) -> None:
        """Analyze class definitions in a file.
        
        Args:
            file_path: Path to the file to analyze
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Visit classes
            visitor = ClassVisitor()
            visitor.visit(tree)
            
            # Store class locations
            for class_name, class_info in visitor.classes.items():
                self.class_locations[class_name].append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "info": class_info
                })
                
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            
    def _find_duplicate_class_definitions(self) -> List[Dict[str, Any]]:
        """Find duplicate class definitions.
        
        Returns:
            List of duplicate class definitions
        """
        duplicates = []
        
        for class_name, locations in self.class_locations.items():
            if len(locations) > 1:
                # Check similarity between all pairs
                similar_pairs = []
                for i, loc1 in enumerate(locations):
                    for j, loc2 in enumerate(locations[i+1:], i+1):
                        similarity = self._calculate_class_definition_similarity(loc1["info"], loc2["info"])
                        if similarity >= self.min_similarity:
                            similar_pairs.append({
                                "file1": loc1["file"],
                                "file2": loc2["file"],
                                "similarity": similarity,
                                "info1": loc1["info"],
                                "info2": loc2["info"]
                            })
                
                if similar_pairs:
                    duplicates.append({
                        'type': 'class_definition',
                        'name': class_name,
                        'pairs': similar_pairs
                    })
        
        return duplicates
        
    def _calculate_class_definition_similarity(self, info1: Dict[str, Any], info2: Dict[str, Any]) -> float:
        """Calculate similarity between two class definitions.
        
        Args:
            info1: First class info
            info2: Second class info
            
        Returns:
            Similarity score (0-1)
        """
        # Compare base classes
        base_similarity = len(set(info1["bases"]) & set(info2["bases"])) / max(
            len(set(info1["bases"]) | set(info2["bases"])), 1
        )
        
        # Compare methods
        method_similarity = len(set(info1["methods"]) & set(info2["methods"])) / max(
            len(set(info1["methods"]) | set(info2["methods"])), 1
        )
        
        # Compare method complexities
        complexity_similarity = 1.0
        if info1["method_complexities"] and info2["method_complexities"]:
            common_methods = set(info1["method_complexities"]) & set(info2["method_complexities"])
            if common_methods:
                complexity_diffs = [
                    abs(info1["method_complexities"][m] - info2["method_complexities"][m])
                    for m in common_methods
                ]
                complexity_similarity = 1.0 - sum(complexity_diffs) / (len(common_methods) * max(complexity_diffs))
        
        # Weighted average
        return (
            0.3 * base_similarity +
            0.4 * method_similarity +
            0.3 * complexity_similarity
        )
    
    def _find_duplicate_functions(self) -> List[Dict[str, Any]]:
        """Find duplicate functions across modules.
        
        Returns:
            List of duplicate function pairs
        """
        duplicates = []
        processed = set()
        
        for module1 in self.modules.values():
            for func1_name, func1 in module1.functions.items():
                for module2 in self.modules.values():
                    if module1.path == module2.path:
                        continue
                        
                    for func2_name, func2 in module2.functions.items():
                        pair = tuple(sorted([(module1.path, func1_name), (module2.path, func2_name)]))
                        if pair in processed:
                            continue
                            
                        similarity = self._calculate_function_similarity(func1, func2)
                        if similarity >= self.min_similarity:
                            duplicates.append({
                                'type': 'function',
                                'similarity': similarity,
                                'items': [
                                    {
                                        'file': str(module1.path),
                                        'name': func1_name,
                                        'complexity': func1.complexity,
                                        'dependencies': list(func1.dependencies)
                                    },
                                    {
                                        'file': str(module2.path),
                                        'name': func2_name,
                                        'complexity': func2.complexity,
                                        'dependencies': list(func2.dependencies)
                                    }
                                ]
                            })
                            processed.add(pair)
        
        return duplicates
    
    def _find_duplicate_classes(self) -> List[Dict[str, Any]]:
        """Find duplicate classes across modules.
        
        Returns:
            List of duplicate class pairs
        """
        duplicates = []
        processed = set()
        
        for module1 in self.modules.values():
            for class1_name, class1 in module1.classes.items():
                for module2 in self.modules.values():
                    if module1.path == module2.path:
                        continue
                        
                    for class2_name, class2 in module2.classes.items():
                        pair = tuple(sorted([(module1.path, class1_name), (module2.path, class2_name)]))
                        if pair in processed:
                            continue
                            
                        similarity = self._calculate_class_similarity(class1, class2)
                        if similarity >= self.min_similarity:
                            duplicates.append({
                                'type': 'class',
                                'similarity': similarity,
                                'items': [
                                    {
                                        'file': str(module1.path),
                                        'name': class1_name,
                                        'methods': class1.methods,
                                        'base_classes': class1.base_classes,
                                        'complexity': class1.complexity,
                                        'dependencies': list(class1.dependencies)
                                    },
                                    {
                                        'file': str(module2.path),
                                        'name': class2_name,
                                        'methods': class2.methods,
                                        'base_classes': class2.base_classes,
                                        'complexity': class2.complexity,
                                        'dependencies': list(class2.dependencies)
                                    }
                                ]
                            })
                            processed.add(pair)
        
        return duplicates
    
    def _find_duplicate_blocks(self) -> List[Dict[str, Any]]:
        """Find duplicate code blocks across files.
        
        Returns:
            List of duplicate code blocks
        """
        duplicates = []
        processed = set()
        
        # Get all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        # Compare each pair of files
        for i, file1 in enumerate(python_files):
            if self._should_skip_file(file1):
                continue
                
            with open(file1, 'r') as f1:
                lines1 = f1.readlines()
                
            for file2 in python_files[i+1:]:
                if self._should_skip_file(file2):
                    continue
                    
                with open(file2, 'r') as f2:
                    lines2 = f2.readlines()
                
                # Find similar blocks
                matcher = SequenceMatcher(None, lines1, lines2)
                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    if tag == 'equal' and (i2 - i1) >= self.min_lines:
                        block1 = ''.join(lines1[i1:i2])
                        block2 = ''.join(lines2[j1:j2])
                        
                        # Calculate similarity
                        similarity = matcher.ratio()
                        if similarity >= self.min_similarity:
                            pair = tuple(sorted([(file1, i1, i2), (file2, j1, j2)]))
                            if pair not in processed:
                                duplicates.append({
                                    'type': 'block',
                                    'similarity': similarity,
                                    'items': [
                                        {
                                            'file': str(file1),
                                            'start_line': i1 + 1,
                                            'end_line': i2,
                                            'content': block1
                                        },
                                        {
                                            'file': str(file2),
                                            'start_line': j1 + 1,
                                            'end_line': j2,
                                            'content': block2
                                        }
                                    ]
                                })
                                processed.add(pair)
        
        return duplicates
    
    def _calculate_function_similarity(self, func1: FunctionInfo, func2: FunctionInfo) -> float:
        """Calculate similarity between two functions.
        
        Args:
            func1: First function info
            func2: Second function info
            
        Returns:
            Similarity score (0-1)
        """
        # Compare complexity
        complexity_similarity = 1.0 - abs(func1.complexity - func2.complexity) / max(
            func1.complexity, func2.complexity, 1
        )
        
        # Compare dependencies
        dep_similarity = len(func1.dependencies & func2.dependencies) / len(
            func1.dependencies | func2.dependencies
        ) if func1.dependencies or func2.dependencies else 1.0
        
        # Weighted average
        return 0.7 * complexity_similarity + 0.3 * dep_similarity
    
    def _calculate_class_similarity(self, class1: ClassInfo, class2: ClassInfo) -> float:
        """Calculate similarity between two classes.
        
        Args:
            class1: First class info
            class2: Second class info
            
        Returns:
            Similarity score (0-1)
        """
        # Compare methods
        methods1 = set(class1.methods)
        methods2 = set(class2.methods)
        method_similarity = len(methods1 & methods2) / len(methods1 | methods2) if methods1 or methods2 else 1.0
        
        # Compare base classes
        bases1 = set(class1.base_classes)
        bases2 = set(class2.base_classes)
        base_similarity = len(bases1 & bases2) / len(bases1 | bases2) if bases1 or bases2 else 1.0
        
        # Compare complexity
        complexity_similarity = 1.0 - abs(class1.complexity - class2.complexity) / max(
            class1.complexity, class2.complexity, 1
        )
        
        # Compare dependencies
        dep_similarity = len(class1.dependencies & class2.dependencies) / len(
            class1.dependencies | class2.dependencies
        ) if class1.dependencies or class2.dependencies else 1.0
        
        # Weighted average
        return (
            0.4 * method_similarity +
            0.2 * base_similarity +
            0.2 * complexity_similarity +
            0.2 * dep_similarity
        )
    
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
            
        # Skip files in test directories
        if 'test' in file_path.parts:
            return True
            
        return False 