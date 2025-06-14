"""
Architectural Analyzer
---------------------
Analyzes code architecture, design patterns, module dependencies, and code structure.
"""

from pathlib import Path
from typing import Dict, List, Set, Any
import logging
import re

from .base_analyzer import BaseAnalyzer, ModuleInfo, ClassInfo, FunctionInfo

logger = logging.getLogger(__name__)

class ArchitecturalAnalyzer(BaseAnalyzer):
    """Analyzes code architecture, design patterns, and structure."""
    
    def __init__(self, project_root: Path):
        """Initialize architectural analyzer.
        
        Args:
            project_root: Root directory of the project
        """
        super().__init__(project_root)
        
        # Design pattern detection
        self.design_patterns = {
            'singleton': r'class\s+\w+\(.*\):\s+.*_instance\s*=\s*None',
            'factory': r'class\s+\w+Factory',
            'observer': r'class\s+\w+Observer|class\s+\w+Subject',
            'decorator': r'@\w+.*\n\s*def\s+\w+',
            'adapter': r'class\s+\w+Adapter',
            'strategy': r'class\s+\w+Strategy',
            'command': r'class\s+\w+Command',
            'template': r'class\s+\w+Template',
            'proxy': r'class\s+\w+Proxy',
            'facade': r'class\s+\w+Facade'
        }
        
        # Standard code organization
        self.standard_layout = [
            'imports',
            'constants',
            'types',
            'classes',
            'functions'
        ]
        
        # Architectural layers
        self.layers = {
            'core': ['core/', 'base/'],
            'services': ['services/', 'api/'],
            'models': ['models/', 'entities/'],
            'utils': ['utils/', 'helpers/']
        }
        
        # Layer dependency rules
        self.layer_rules = {
            'core': ['utils'],
            'services': ['core', 'models', 'utils'],
            'models': ['utils'],
            'utils': []
        }
        
    def analyze_architecture(self) -> Dict[str, Any]:
        """Analyze code architecture across the project.
        
        Returns:
            Dictionary containing architectural analysis results
        """
        results = {
            'design_patterns': self._find_design_patterns(),
            'architectural_issues': self._find_architectural_issues(),
            'module_dependencies': self._analyze_module_dependencies(),
            'layer_violations': self._check_layer_violations(),
            'circular_dependencies': self._find_circular_dependencies(),
            'structure': {
                'module_structure': self._analyze_module_structure(),
                'file_organization': self._analyze_file_organization(),
                'structural_issues': self._find_structural_issues(),
                'naming_conventions': self._check_naming_conventions(),
                'code_organization': self._analyze_code_organization()
            }
        }
        
        return results
        
    def _find_design_patterns(self) -> List[Dict[str, Any]]:
        """Find design patterns in the codebase.
        
        Returns:
            List of found design patterns with details
        """
        patterns = []
        
        for module_info in self.modules.values():
            source_code = module_info.path.read_text()
            
            for pattern_name, pattern_regex in self.design_patterns.items():
                matches = re.finditer(pattern_regex, source_code, re.MULTILINE)
                for match in matches:
                    patterns.append({
                        'pattern': pattern_name,
                        'file': str(module_info.path),
                        'line': source_code[:match.start()].count('\n') + 1,
                        'context': match.group(0).strip()
                    })
        
        return patterns
        
    def _find_architectural_issues(self) -> List[Dict[str, Any]]:
        """Find potential architectural issues.
        
        Returns:
            List of architectural issues with details
        """
        issues = []
        
        for module_info in self.modules.values():
            # Check for large modules
            if module_info.lines > 1000:
                issues.append({
                    'type': 'large_module',
                    'file': str(module_info.path),
                    'lines': module_info.lines,
                    'description': 'Module exceeds 1000 lines'
                })
            
            # Check for high complexity
            if module_info.complexity > 50:
                issues.append({
                    'type': 'high_complexity',
                    'file': str(module_info.path),
                    'complexity': module_info.complexity,
                    'description': 'Module has high cyclomatic complexity'
                })
            
            # Check for too many dependencies
            if len(module_info.imports) > 20:
                issues.append({
                    'type': 'many_dependencies',
                    'file': str(module_info.path),
                    'dependencies': len(module_info.imports),
                    'description': 'Module has too many dependencies'
                })
            
            # Check for deep inheritance
            for class_info in module_info.classes.values():
                if len(class_info.bases) > 2:
                    issues.append({
                        'type': 'deep_inheritance',
                        'file': str(module_info.path),
                        'class': class_info.name,
                        'depth': len(class_info.bases),
                        'description': 'Class has deep inheritance hierarchy'
                    })
        
        return issues
        
    def _analyze_module_dependencies(self) -> Dict[str, List[str]]:
        """Analyze dependencies between modules.
        
        Returns:
            Dictionary mapping modules to their dependencies
        """
        dependencies = {}
        
        for module_info in self.modules.values():
            module_deps = set()
            
            # Add direct imports
            for imp in module_info.imports:
                if imp.startswith('.'):
                    # Relative import
                    module_deps.add(str(module_info.path.parent / imp[1:]))
                else:
                    # Absolute import
                    module_deps.add(imp)
            
            # Add dependencies from classes and functions
            for class_info in module_info.classes.values():
                module_deps.update(class_info.dependencies)
            
            for func_info in module_info.functions.values():
                module_deps.update(func_info.dependencies)
            
            dependencies[str(module_info.path)] = sorted(module_deps)
        
        return dependencies
        
    def _check_layer_violations(self) -> List[Dict[str, Any]]:
        """Check for violations of architectural layers.
        
        Returns:
            List of layer violations with details
        """
        violations = []
        
        for module_info in self.modules.values():
            module_path = str(module_info.path)
            
            # Determine module's layer
            module_layer = None
            for layer, patterns in self.layers.items():
                if any(pattern in module_path for pattern in patterns):
                    module_layer = layer
                    break
            
            if module_layer:
                # Check dependencies against layer rules
                for dep in module_info.imports:
                    dep_layer = None
                    for layer, patterns in self.layers.items():
                        if any(pattern in dep for pattern in patterns):
                            dep_layer = layer
                            break
                    
                    if dep_layer and self._is_layer_violation(module_layer, dep_layer):
                        violations.append({
                            'type': 'layer_violation',
                            'file': module_path,
                            'module_layer': module_layer,
                            'dependency': dep,
                            'dependency_layer': dep_layer,
                            'description': f'Module in {module_layer} layer depends on {dep_layer} layer'
                        })
        
        return violations
        
    def _is_layer_violation(self, source_layer: str, target_layer: str) -> bool:
        """Check if a dependency between layers is a violation.
        
        Args:
            source_layer: Source module's layer
            target_layer: Target module's layer
            
        Returns:
            True if the dependency violates layer rules
        """
        return target_layer not in self.layer_rules.get(source_layer, [])
        
    def _find_circular_dependencies(self) -> List[Dict[str, Any]]:
        """Find circular dependencies between modules.
        
        Returns:
            List of circular dependencies with details
        """
        circular = []
        visited = set()
        path = []
        
        def visit(module_path: str):
            if module_path in path:
                cycle = path[path.index(module_path):]
                circular.append({
                    'type': 'circular_dependency',
                    'cycle': cycle,
                    'description': f'Circular dependency detected: {" -> ".join(cycle)}'
                })
                return
            
            if module_path in visited:
                return
                
            visited.add(module_path)
            path.append(module_path)
            
            for dep in self.modules[Path(module_path)].imports:
                if dep in self.modules:
                    visit(str(self.modules[dep].path))
            
            path.pop()
        
        for module_path in self.modules:
            if str(module_path) not in visited:
                visit(str(module_path))
        
        return circular
        
    def _analyze_module_structure(self) -> Dict[str, Dict[str, Any]]:
        """Analyze structure of each module.
        
        Returns:
            Dictionary mapping modules to their structure details
        """
        structure = {}
        
        for module_info in self.modules.values():
            module_structure = {
                'imports': len(module_info.imports),
                'classes': len(module_info.classes),
                'functions': len(module_info.functions),
                'total_lines': module_info.lines,
                'complexity': module_info.complexity,
                'dependencies': len(module_info.imports)
            }
            
            # Calculate class and function distribution
            class_sizes = [len(c.methods) for c in module_info.classes.values()]
            function_sizes = [f.lines for f in module_info.functions.values()]
            
            module_structure.update({
                'avg_class_size': sum(class_sizes) / len(class_sizes) if class_sizes else 0,
                'avg_function_size': sum(function_sizes) / len(function_sizes) if function_sizes else 0,
                'max_class_size': max(class_sizes) if class_sizes else 0,
                'max_function_size': max(function_sizes) if function_sizes else 0
            })
            
            structure[str(module_info.path)] = module_structure
        
        return structure
        
    def _analyze_file_organization(self) -> List[Dict[str, Any]]:
        """Analyze file organization and layout.
        
        Returns:
            List of file organization details
        """
        organization = []
        
        for module_info in self.modules.values():
            try:
                with open(module_info.path) as f:
                    lines = f.readlines()
                
                # Find section boundaries
                sections = {
                    'imports': [],
                    'constants': [],
                    'types': [],
                    'classes': [],
                    'functions': []
                }
                
                current_section = None
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                        
                    if line.startswith('import ') or line.startswith('from '):
                        current_section = 'imports'
                    elif re.match(r'^[A-Z_]+ = ', line):
                        current_section = 'constants'
                    elif line.startswith('class '):
                        current_section = 'classes'
                    elif line.startswith('def '):
                        current_section = 'functions'
                    elif line.startswith('Type') or line.startswith('type '):
                        current_section = 'types'
                        
                    if current_section:
                        sections[current_section].append(i + 1)
                
                # Check section order
                section_order = []
                for line_num in range(1, len(lines) + 1):
                    for section, lines in sections.items():
                        if line_num in lines:
                            section_order.append(section)
                            break
                
                organization.append({
                    'file': str(module_info.path),
                    'sections': sections,
                    'section_order': section_order,
                    'follows_standard': self._check_section_order(section_order)
                })
                
            except Exception as e:
                logger.error(f"Error analyzing file organization for {module_info.path}: {e}")
        
        return organization
        
    def _find_structural_issues(self) -> List[Dict[str, Any]]:
        """Find structural issues in the codebase.
        
        Returns:
            List of structural issues with details
        """
        issues = []
        
        for module_info in self.modules.values():
            # Check for mixed concerns
            if len(module_info.classes) > 0 and len(module_info.functions) > 10:
                issues.append({
                    'type': 'mixed_concerns',
                    'file': str(module_info.path),
                    'classes': len(module_info.classes),
                    'functions': len(module_info.functions),
                    'description': 'Module mixes classes and many functions'
                })
            
            # Check for large classes
            for class_info in module_info.classes.values():
                if len(class_info.methods) > 20:
                    issues.append({
                        'type': 'large_class',
                        'file': str(module_info.path),
                        'class': class_info.name,
                        'methods': len(class_info.methods),
                        'description': 'Class has too many methods'
                    })
            
            # Check for long functions
            for func_info in module_info.functions.values():
                if func_info.lines > 50:
                    issues.append({
                        'type': 'long_function',
                        'file': str(module_info.path),
                        'function': func_info.name,
                        'lines': func_info.lines,
                        'description': 'Function is too long'
                    })
            
            # Check for inconsistent indentation
            try:
                with open(module_info.path) as f:
                    lines = f.readlines()
                
                indent_sizes = set()
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        if indent > 0:
                            indent_sizes.add(indent)
                
                if len(indent_sizes) > 2:
                    issues.append({
                        'type': 'inconsistent_indentation',
                        'file': str(module_info.path),
                        'indent_sizes': sorted(indent_sizes),
                        'description': 'Inconsistent indentation found'
                    })
                    
            except Exception as e:
                logger.error(f"Error checking indentation for {module_info.path}: {e}")
        
        return issues
        
    def _check_naming_conventions(self) -> List[Dict[str, Any]]:
        """Check naming conventions across the codebase.
        
        Returns:
            List of naming convention violations
        """
        violations = []
        
        for module_info in self.modules.values():
            # Check module name
            if not re.match(r'^[a-z][a-z0-9_]*$', module_info.path.stem):
                violations.append({
                    'type': 'module_naming',
                    'file': str(module_info.path),
                    'name': module_info.path.stem,
                    'description': 'Module name should be lowercase with underscores'
                })
            
            # Check class names
            for class_info in module_info.classes.values():
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', class_info.name):
                    violations.append({
                        'type': 'class_naming',
                        'file': str(module_info.path),
                        'class': class_info.name,
                        'description': 'Class name should be CamelCase'
                    })
                
                # Check method names
                for method in class_info.methods:
                    if not re.match(r'^[a-z][a-z0-9_]*$', method):
                        violations.append({
                            'type': 'method_naming',
                            'file': str(module_info.path),
                            'class': class_info.name,
                            'method': method,
                            'description': 'Method name should be lowercase with underscores'
                        })
            
            # Check function names
            for func_info in module_info.functions.values():
                if not re.match(r'^[a-z][a-z0-9_]*$', func_info.name):
                    violations.append({
                        'type': 'function_naming',
                        'file': str(module_info.path),
                        'function': func_info.name,
                        'description': 'Function name should be lowercase with underscores'
                    })
        
        return violations
        
    def _analyze_code_organization(self) -> Dict[str, Any]:
        """Analyze overall code organization.
        
        Returns:
            Dictionary containing code organization analysis
        """
        return {
            'module_distribution': self._analyze_module_distribution(),
            'dependency_graph': self._build_dependency_graph(),
            'layer_distribution': self._analyze_layer_distribution()
        }
        
    def _analyze_module_distribution(self) -> Dict[str, int]:
        """Analyze distribution of modules across the project.
        
        Returns:
            Dictionary mapping module types to counts
        """
        distribution = {
            'core': 0,
            'services': 0,
            'models': 0,
            'utils': 0,
            'tests': 0,
            'other': 0
        }
        
        for module_info in self.modules.values():
            module_path = str(module_info.path)
            
            if 'test' in module_path.lower():
                distribution['tests'] += 1
            else:
                found = False
                for layer, patterns in self.layers.items():
                    if any(pattern in module_path for pattern in patterns):
                        distribution[layer] += 1
                        found = True
                        break
                if not found:
                    distribution['other'] += 1
        
        return distribution
        
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a graph of module dependencies.
        
        Returns:
            Dictionary mapping modules to their dependencies
        """
        graph = {}
        
        for module_info in self.modules.values():
            module_path = str(module_info.path)
            dependencies = set()
            
            # Add direct imports
            for imp in module_info.imports:
                if imp.startswith('.'):
                    # Relative import
                    dep_path = str(module_info.path.parent / imp[1:])
                    if dep_path in self.modules:
                        dependencies.add(dep_path)
                else:
                    # Absolute import
                    if imp in self.modules:
                        dependencies.add(str(self.modules[imp].path))
            
            graph[module_path] = sorted(dependencies)
        
        return graph
        
    def _analyze_layer_distribution(self) -> Dict[str, Dict[str, int]]:
        """Analyze distribution of code across layers.
        
        Returns:
            Dictionary containing layer statistics
        """
        distribution = {
            layer: {
                'modules': 0,
                'classes': 0,
                'functions': 0,
                'lines': 0
            }
            for layer in self.layers
        }
        
        for module_info in self.modules.values():
            module_path = str(module_info.path)
            
            # Determine module's layer
            module_layer = None
            for layer, patterns in self.layers.items():
                if any(pattern in module_path for pattern in patterns):
                    module_layer = layer
                    break
            
            if module_layer:
                distribution[module_layer]['modules'] += 1
                distribution[module_layer]['classes'] += len(module_info.classes)
                distribution[module_layer]['functions'] += len(module_info.functions)
                distribution[module_layer]['lines'] += module_info.lines
        
        return distribution
        
    def _check_section_order(self, section_order: List[str]) -> bool:
        """Check if section order follows standard layout.
        
        Args:
            section_order: List of sections in order of appearance
            
        Returns:
            True if section order follows standard layout
        """
        # Remove duplicates while preserving order
        seen = set()
        unique_order = [x for x in section_order if not (x in seen or seen.add(x))]
        
        # Check if order matches standard layout
        for i, section in enumerate(unique_order):
            if i >= len(self.standard_layout):
                return False
            if section != self.standard_layout[i]:
                return False
        
        return True 