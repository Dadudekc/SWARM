import ast
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from ..models.analysis import ClassInfo

logger = logging.getLogger(__name__)

class ASTAnalyzer:
    """Analyzes Python source code using AST."""
    
    def __init__(self):
        self.functions: List[str] = []
        self.classes: Dict[str, ClassInfo] = {}
        
    def analyze(self, source_code: str) -> Tuple[List[str], Dict[str, ClassInfo]]:
        """Analyze source code and extract functions and classes.
        
        Args:
            source_code: The source code to analyze
            
        Returns:
            Tuple containing:
            - List of function names
            - Dictionary of class information
        """
        try:
            tree = ast.parse(source_code)
            self._reset_state()
            self._analyze_tree(tree)
            return self.functions, self.classes
        except SyntaxError as e:
            logger.error(f"Syntax error in source code: {e}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing AST: {e}")
            raise
            
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