"""
AST Analyzer
-----------
Specialized analyzer for AST-based code analysis and pattern detection.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
import logging

from .base_analyzer import BaseAnalyzer, ModuleInfo, ClassInfo, FunctionInfo

logger = logging.getLogger(__name__)

class ASTAnalyzer(BaseAnalyzer):
    """Analyzes Python source code using AST for pattern detection and analysis."""
    
    def analyze_source(self, source_code: str) -> ModuleInfo:
        """Analyze source code directly.
        
        Args:
            source_code: The source code to analyze
            
        Returns:
            ModuleInfo containing analysis results
        """
        try:
            tree = ast.parse(source_code)
            module_info = ModuleInfo(path=Path("memory"))
            
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
            module_info.lines = len(source_code.splitlines())
            
            return module_info
            
        except SyntaxError as e:
            logger.error(f"Syntax error in source code: {e}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing AST: {e}")
            raise
    
    def find_patterns(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Find specific patterns in the code.
        
        Args:
            pattern_type: Type of pattern to find ('decorator', 'context', etc.)
            
        Returns:
            List of found patterns
        """
        patterns = []
        
        for module_info in self.modules.values():
            for node in ast.walk(ast.parse(module_info.path.read_text())):
                if self._matches_pattern(node, pattern_type):
                    patterns.append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'pattern': pattern_type,
                        'details': self._extract_pattern_details(node)
                    })
        
        return patterns
    
    def find_all_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Find all supported patterns in the code.
        
        Returns:
            Dictionary mapping pattern types to lists of found patterns
        """
        results = {
            'decorators': [],
            'context_managers': [],
            'async_code': [],
            'comprehensions': [],
            'type_hints': [],
            'docstrings': []
        }
        
        for module_info in self.modules.values():
            tree = ast.parse(module_info.path.read_text())
            for node in ast.walk(tree):
                # Check each pattern type
                if self._matches_pattern(node, 'decorator'):
                    results['decorators'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_pattern_details(node)
                    })
                elif self._matches_pattern(node, 'context'):
                    results['context_managers'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_pattern_details(node)
                    })
                elif self._matches_pattern(node, 'async'):
                    results['async_code'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_pattern_details(node)
                    })
                elif self._matches_pattern(node, 'comprehension'):
                    results['comprehensions'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_pattern_details(node)
                    })
                elif self._has_type_hints(node):
                    results['type_hints'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_type_hints(node)
                    })
                elif self._has_docstring(node):
                    results['docstrings'].append({
                        'file': str(module_info.path),
                        'line': node.lineno,
                        'details': self._extract_docstring(node)
                    })
        
        return results
    
    def _matches_pattern(self, node: ast.AST, pattern_type: str) -> bool:
        """Check if a node matches a specific pattern.
        
        Args:
            node: AST node to check
            pattern_type: Type of pattern to match
            
        Returns:
            True if node matches pattern
        """
        if pattern_type == 'decorator':
            return isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list
        elif pattern_type == 'context':
            return isinstance(node, ast.With)
        elif pattern_type == 'async':
            return isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith))
        elif pattern_type == 'comprehension':
            return isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
        return False
    
    def _has_type_hints(self, node: ast.AST) -> bool:
        """Check if a node has type hints.
        
        Args:
            node: AST node to check
            
        Returns:
            True if node has type hints
        """
        if isinstance(node, ast.FunctionDef):
            return bool(node.returns or any(arg.annotation for arg in node.args.args))
        elif isinstance(node, ast.ClassDef):
            return any(isinstance(n, ast.AnnAssign) for n in node.body)
        return False
    
    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if a node has a docstring.
        
        Args:
            node: AST node to check
            
        Returns:
            True if node has a docstring
        """
        return bool(ast.get_docstring(node))
    
    def _extract_pattern_details(self, node: ast.AST) -> Dict[str, Any]:
        """Extract details about a matched pattern.
        
        Args:
            node: AST node that matched a pattern
            
        Returns:
            Dictionary of pattern details
        """
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return {
                'name': node.name,
                'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
            }
        elif isinstance(node, ast.With):
            return {
                'items': [self._extract_with_item(item) for item in node.items]
            }
        elif isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)):
            return {
                'type': node.__class__.__name__,
                'name': getattr(node, 'name', None)
            }
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return {
                'type': node.__class__.__name__,
                'generators': len(node.generators)
            }
        return {}
    
    def _extract_type_hints(self, node: ast.AST) -> Dict[str, Any]:
        """Extract type hints from a node.
        
        Args:
            node: AST node with type hints
            
        Returns:
            Dictionary of type hint details
        """
        if isinstance(node, ast.FunctionDef):
            return {
                'name': node.name,
                'return_type': self._extract_expr(node.returns) if node.returns else None,
                'arg_types': {
                    arg.arg: self._extract_expr(arg.annotation)
                    for arg in node.args.args
                    if arg.annotation
                }
            }
        elif isinstance(node, ast.ClassDef):
            return {
                'name': node.name,
                'field_types': {
                    target.id: self._extract_expr(annotation)
                    for target, annotation in (
                        (n.target, n.annotation)
                        for n in node.body
                        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                    )
                }
            }
        return {}
    
    def _extract_docstring(self, node: ast.AST) -> Dict[str, Any]:
        """Extract docstring details from a node.
        
        Args:
            node: AST node with docstring
            
        Returns:
            Dictionary of docstring details
        """
        docstring = ast.get_docstring(node)
        if docstring:
            return {
                'type': node.__class__.__name__,
                'name': getattr(node, 'name', None),
                'content': docstring,
                'length': len(docstring)
            }
        return {}
    
    def _extract_with_item(self, item: ast.withitem) -> Dict[str, Any]:
        """Extract details from a with statement item.
        
        Args:
            item: with statement item
            
        Returns:
            Dictionary of item details
        """
        return {
            'context_expr': self._extract_expr(item.context_expr),
            'optional_vars': self._extract_expr(item.optional_vars) if item.optional_vars else None
        }
    
    def _extract_expr(self, node: ast.AST) -> str:
        """Extract string representation of an expression.
        
        Args:
            node: AST expression node
            
        Returns:
            String representation of the expression
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_expr(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return f"{self._extract_expr(node.func)}()"
        elif isinstance(node, ast.Subscript):
            return f"{self._extract_expr(node.value)}[{self._extract_expr(node.slice)}]"
        elif isinstance(node, ast.Index):
            return self._extract_expr(node.value)
        return str(node)

    def _reset_state(self):
        """Reset the analyzer state."""
        self.functions = []
        self.classes = {}
        
    def _analyze_tree(self, tree: ast.AST):
        """Analyze the AST tree and extract information."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
            elif isinstance(node, ast.ClassDef):
                self._analyze_class(node)
                
    def _analyze_function(self, node: ast.FunctionDef):
        """Analyze a function definition."""
        self.functions.append(node.name)
        
    def _analyze_class(self, node: ast.ClassDef):
        """Analyze a class definition."""
        docstring = ast.get_docstring(node)
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        base_classes = self._extract_base_classes(node)
        
        self.classes[node.name] = ClassInfo(
            name=node.name,
            methods=methods,
            docstring=docstring,
            base_classes=base_classes,
            maturity='Unknown',
            agent_type='Unknown',
            complexity=0,
            dependencies=set()
        )
        
    def _extract_base_classes(self, node: ast.ClassDef) -> List[str]:
        """Extract base class names from a class definition."""
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
