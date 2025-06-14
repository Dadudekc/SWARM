"""
Code Analyzer
------------
Specialized analyzer for code structure and quality metrics.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import ast

from .base_analyzer import BaseAnalyzer, ModuleInfo, FunctionInfo, ClassInfo

class CodeAnalyzer(BaseAnalyzer):
    """Analyzes code structure and metrics."""
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project.
        
        Returns:
            Dictionary containing project-wide analysis results
        """
        if not self.project_root:
            raise ValueError("Project root not set")
            
        results = {
            'total_files': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0,
            'total_complexity': 0,
            'total_lines': 0,
            'files': {},
            'metrics': {
                'avg_complexity': 0.0,
                'avg_functions_per_file': 0.0,
                'avg_classes_per_file': 0.0,
                'avg_imports_per_file': 0.0,
                'avg_lines_per_file': 0.0
            }
        }
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        results['total_files'] = len(python_files)
        
        # Analyze each file
        for file_path in python_files:
            module_info = self.analyze_file(file_path)
            
            # Update totals
            results['total_functions'] += len(module_info.functions)
            results['total_classes'] += len(module_info.classes)
            results['total_imports'] += len(module_info.imports)
            results['total_complexity'] += module_info.complexity
            results['total_lines'] += module_info.lines
            
            # Store file analysis
            results['files'][str(file_path)] = {
                'functions': list(module_info.functions.keys()),
                'classes': list(module_info.classes.keys()),
                'imports': list(module_info.imports),
                'complexity': module_info.complexity,
                'lines': module_info.lines,
                'metrics': {
                    'functions_per_class': len(module_info.functions) / max(len(module_info.classes), 1),
                    'imports_per_function': len(module_info.imports) / max(len(module_info.functions), 1),
                    'complexity_per_function': module_info.complexity / max(len(module_info.functions), 1)
                }
            }
        
        # Calculate project-wide metrics
        if results['total_files'] > 0:
            results['metrics'].update({
                'avg_complexity': results['total_complexity'] / results['total_files'],
                'avg_functions_per_file': results['total_functions'] / results['total_files'],
                'avg_classes_per_file': results['total_classes'] / results['total_files'],
                'avg_imports_per_file': results['total_imports'] / results['total_files'],
                'avg_lines_per_file': results['total_lines'] / results['total_files']
            })
        
        return results
    
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