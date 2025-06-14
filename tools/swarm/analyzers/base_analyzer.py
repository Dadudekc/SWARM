"""
Base Analyzer Module
------------------
Core functionality for code analysis, providing a foundation for specialized analyzers.
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    methods: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    maturity: str = "Unknown"
    agent_type: str = "Unknown"
    complexity: int = 0
    dependencies: Set[str] = field(default_factory=set)

@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    docstring: Optional[str] = None
    complexity: int = 0
    dependencies: Set[str] = field(default_factory=set)

@dataclass
class ModuleInfo:
    """Information about a Python module."""
    path: Path
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    imports: Set[str] = field(default_factory=set)
    complexity: int = 0
    lines: int = 0

class BaseAnalyzer:
    """Base class for code analyzers."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize analyzer.
        
        Args:
            project_root: Root directory of the project (optional)
        """
        self.project_root = project_root
        self.modules: Dict[Path, ModuleInfo] = {}
        
    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a single file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            ModuleInfo containing analysis results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            tree = ast.parse(source)
            module_info = ModuleInfo(path=file_path)
            
            # Extract imports
            module_info.imports = self._extract_imports(tree)
            
            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    module_info.functions[node.name] = self._analyze_function(node)
                elif isinstance(node, ast.ClassDef):
                    module_info.classes[node.name] = self._analyze_class(node)
            
            # Calculate metrics
            module_info.complexity = self._calculate_complexity(tree)
            module_info.lines = len(source.splitlines())
            
            # Cache results
            self.modules[file_path] = module_info
            
            return module_info
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return ModuleInfo(path=file_path)
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST.
        
        Args:
            tree: AST to analyze
            
        Returns:
            Set of imported module names
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    
        return imports
    
    def _analyze_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Analyze a function definition.
        
        Args:
            node: Function definition node
            
        Returns:
            FunctionInfo containing analysis results
        """
        return FunctionInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            complexity=self._calculate_node_complexity(node),
            dependencies=self._extract_function_dependencies(node)
        )
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition.
        
        Args:
            node: Class definition node
            
        Returns:
            ClassInfo containing analysis results
        """
        methods = []
        dependencies = set()
        
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                methods.append(child.name)
                dependencies.update(self._extract_function_dependencies(child))
        
        return ClassInfo(
            name=node.name,
            methods=methods,
            docstring=ast.get_docstring(node),
            base_classes=self._extract_base_classes(node),
            complexity=self._calculate_node_complexity(node),
            dependencies=dependencies
        )
    
    def _extract_base_classes(self, node: ast.ClassDef) -> List[str]:
        """Extract base class names from a class definition.
        
        Args:
            node: Class definition node
            
        Returns:
            List of base class names
        """
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_parts = []
                attr_node = base
                while isinstance(attr_node, ast.Attribute):
                    base_parts.append(attr_node.attr)
                    attr_node = attr_node.value
                if isinstance(attr_node, ast.Name):
                    base_parts.append(attr_node.id)
                base_classes.append(".".join(reversed(base_parts)))
        return base_classes
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST.
        
        Args:
            tree: AST to analyze
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try,
                               ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
                
        return complexity
    
    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of a specific AST node.
        
        Args:
            node: AST node to analyze
            
        Returns:
            Complexity score
        """
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try,
                                ast.ExceptHandler, ast.With, ast.Assert)):
                complexity += 1
                
        return complexity
    
    def _extract_function_dependencies(self, node: ast.AST) -> Set[str]:
        """Extract dependencies from a function definition.
        
        Args:
            node: Function definition node
            
        Returns:
            Set of dependency names
        """
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Load):
                    dependencies.add(child.id)
                    
        return dependencies
    
    def get_module_info(self, file_path: Path) -> Optional[ModuleInfo]:
        """Get cached module information.
        
        Args:
            file_path: Path to the module
            
        Returns:
            ModuleInfo if available, None otherwise
        """
        return self.modules.get(file_path)
    
    def clear_cache(self):
        """Clear the module cache."""
        self.modules.clear() 