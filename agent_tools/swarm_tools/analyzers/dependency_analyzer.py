import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
import networkx as nx
from ..models.analysis import FileAnalysis, ProjectAnalysis

class DependencyAnalyzer:
    """Analyzes dependencies between files and detects circular dependencies."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).absolute()
        self.dependency_graph = nx.DiGraph()
        
    def analyze_dependencies(self, files: Dict[str, any]) -> Tuple[Dict[str, Set[str]], List[List[str]]]:
        """Build dependency graph and detect circular dependencies."""
        # Normalize all file keys to absolute paths
        abs_files = {str(Path(k).absolute()): v for k, v in files.items()}
        
        # Build dependency graph
        self.dependency_graph.clear()
        dependencies = {}
        
        # Create a mapping of module names to file paths
        module_map = {}
        for file in abs_files:
            file_path = Path(file)
            # Add both the full path and the module name
            module_map[str(file_path)] = file
            module_map[file_path.stem] = file
            # Add the relative path from project root
            try:
                rel_path = file_path.relative_to(self.project_root)
                module_map[str(rel_path).replace('\\', '/').replace('/', '.')] = file
                module_map[str(rel_path).replace('\\', '/').replace('/', '.')[:-3]] = file  # Remove .py
            except ValueError:
                pass
        
        for file, analysis in abs_files.items():
            file_deps = set()
            file_path = Path(file)
            file_dir = file_path.parent
            
            for imp in analysis.imports:
                # Handle relative imports
                if imp.startswith('.'):
                    # Count dots to determine relative level
                    dots = len(imp.split('.')[0])
                    # Get the base directory for relative import
                    base_dir = file_dir
                    for _ in range(dots - 1):
                        base_dir = base_dir.parent
                    
                    # Try to resolve the import
                    import_path = base_dir / imp.replace('.', '/').lstrip('.')
                    if import_path.suffix == '':
                        import_path = import_path.with_suffix('.py')
                    
                    # Find matching file
                    for other_file in abs_files:
                        if other_file == file:
                            continue
                        other_path = Path(other_file)
                        if other_path == import_path or other_path.stem == import_path.stem:
                            file_deps.add(other_file)
                            self.dependency_graph.add_edge(file, other_file)
                else:
                    # Handle absolute imports
                    # Try to find the module in our mapping
                    if imp in module_map:
                        other_file = module_map[imp]
                        if other_file != file:
                            file_deps.add(other_file)
                            self.dependency_graph.add_edge(file, other_file)
                    else:
                        # Try partial matches
                        for module_name, other_file in module_map.items():
                            if imp in module_name or module_name in imp:
                                if other_file != file:
                                    file_deps.add(other_file)
                                    self.dependency_graph.add_edge(file, other_file)
            
            dependencies[file] = file_deps
            
        # Detect cycles
        cycles = list(nx.simple_cycles(self.dependency_graph))
        return dependencies, cycles
        
    def analyze_file_dependencies(self, file_path: Path, source_code: str) -> Set[str]:
        """Extract dependencies from a single file."""
        try:
            tree = ast.parse(source_code)
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
            return imports
        except Exception as e:
            print(f"Error analyzing dependencies in {file_path}: {e}")
            return set()
            
    def identify_core_components(self, files: Dict[str, any], dependencies: Dict[str, Set[str]]):
        """Identify core components of the dependency graph."""
        # Normalize all file keys to absolute paths
        abs_files = [str(Path(f).absolute()) for f in files]
        core = set()
        peripheral = set()
        
        # First pass: identify core components
        for file in abs_files:
            if file not in self.dependency_graph:
                continue
            in_deg = self.dependency_graph.in_degree[file]
            out_deg = self.dependency_graph.out_degree[file]
            if in_deg > 0 and out_deg > 0:
                core.add(file)
        
        # Second pass: identify peripheral components
        for file in abs_files:
            if file not in core:
                peripheral.add(file)
        
        # If no core components found, make the first file core
        if not core and abs_files:
            first = abs_files[0]
            core.add(first)
            for f in abs_files:
                if f != first:
                    peripheral.add(f)
                    
        return core, peripheral
        
    def group_into_modules(self, files: Dict[str, any]) -> Dict[str, Set[str]]:
        """Group files into modules based on directory structure and dependencies."""
        modules = {}
        for file in files:
            module = str(Path(file).parent)
            modules.setdefault(module, set()).add(file)
        return modules 
