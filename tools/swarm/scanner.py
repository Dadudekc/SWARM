"""
Unified Scanner Module
--------------------
Core module for scanning and analyzing code, combining functionality from multiple implementations.
"""

import ast
import json
import logging
import time
import asyncio
import argparse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScanResults:
    """Results from a code scan."""
    total_files: int = 0
    total_duplicates: int = 0
    duplicates: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    narrative: str = ""
    top_violators: List[Dict[str, Any]] = field(default_factory=list)
    scan_time: float = 0.0
    project_analysis: Dict[str, Any] = field(default_factory=dict)
    architectural_issues: List[Dict[str, Any]] = field(default_factory=list)
    structural_insights: List[Dict[str, Any]] = field(default_factory=list)
    themes: List[Dict[str, Any]] = field(default_factory=list)
    init_files: List[str] = field(default_factory=list)
    
    def save_reports(self, output_dir: Optional[str] = None) -> bool:
        """Save scan results to files."""
        try:
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path = Path("reports")
                output_path.mkdir(exist_ok=True)
            
            # Save project analysis
            project_analysis = {
                "project_root": str(Path.cwd()),
                "num_files_analyzed": self.total_files,
                "analysis_details": self.project_analysis,
                "architectural_issues": self.architectural_issues,
                "structural_insights": self.structural_insights,
                "themes": self.themes
            }
            
            with open(output_path / "project_analysis.json", 'w') as f:
                json.dump(project_analysis, f, indent=4)
            
            # Save duplicates report
            duplicates_report = {
                "total_duplicates": self.total_duplicates,
                "duplicates": self.duplicates,
                "top_violators": self.top_violators
            }
            
            with open(output_path / "duplicates_report.json", 'w') as f:
                json.dump(duplicates_report, f, indent=4)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving reports: {str(e)}")
            return False

class Scanner:
    """Unified code scanner for detecting duplicates and analyzing code structure."""
    
    def __init__(self, project_root: str, output_dir: Optional[str] = None, 
                 similarity_threshold: float = 0.8, safe_mode: bool = True):
        """Initialize scanner.
        
        Args:
            project_root: Root directory of the project to scan
            output_dir: Directory to write reports to
            similarity_threshold: Minimum similarity score (0-1) to consider code similar
            safe_mode: Whether to use safe mode with strict path filtering
        """
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir) if output_dir else self.project_root / 'reports'
        self.similarity_threshold = similarity_threshold
        self.safe_mode = safe_mode
        self.logger = logging.getLogger(__name__)
        
    async def scan(self, categorize_agents: bool = False, generate_init: bool = False) -> ScanResults:
        """Run a full scan of the project.
        
        Args:
            categorize_agents: Whether to categorize agents
            generate_init: Whether to generate __init__.py files
            
        Returns:
            ScanResults object containing scan results
        """
        start_time = time.time()
        results = ScanResults()
        
        try:
            # Get all Python files
            python_files = list(self.project_root.rglob("*.py"))
            results.total_files = len(python_files)
            
            # Skip test files, __init__.py, and virtual environment
            python_files = [
                f for f in python_files 
                if not f.name.startswith("test_") 
                and f.name != "__init__.py"
                and ".venv" not in str(f)
            ]
            
            # Generate __init__.py files if requested
            if generate_init:
                results.init_files = self._generate_init_files()
                # Add generated __init__.py files to the count
                for init_file in results.init_files:
                    init_path = self.project_root / init_file
                    if init_path not in python_files:
                        python_files.append(init_path)
            
            # Analyze each file
            all_node_dicts = []
            all_ast_nodes = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Extract nodes
                    node_dicts = self._extract_nodes(tree, content, file_path)
                    all_node_dicts.extend(node_dicts)
                    all_ast_nodes.extend([d['ast_node'] for d in node_dicts if 'ast_node' in d])
                    
                    # Add to project analysis
                    results.project_analysis[str(file_path)] = self._analyze_file(tree, content)
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing {file_path}: {str(e)}")
                    continue
            
            # Find duplicates
            results.duplicates = self._find_duplicates(all_node_dicts)
            results.total_duplicates = sum(len(d) for d in results.duplicates.values())
            
            # Analyze architectural issues
            results.architectural_issues = self._analyze_architecture(all_node_dicts)
            
            # Analyze structural patterns
            results.structural_insights = self._analyze_structure(all_ast_nodes)
            
            # Analyze themes
            results.themes = self._analyze_themes(all_node_dicts)
            
            # Find top violators
            results.top_violators = self._find_top_violators(results)
            
            # Generate narrative
            results.narrative = self._generate_narrative(results)
            
            # Calculate scan time
            results.scan_time = time.time() - start_time
            
            # Save reports
            results.save_reports(self.output_dir)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Scan failed: {str(e)}")
            raise
    
    def _extract_nodes(self, tree: ast.AST, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Extract nodes from AST."""
        nodes = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                node_dict = {
                    'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
                    'name': node.name,
                    'file': str(file_path),
                    'ast_node': node
                }
                
                if isinstance(node, ast.FunctionDef):
                    node_dict['source'] = ast.get_source_segment(content, node)
                else:
                    node_dict['methods'] = [
                        child.name for child in node.body 
                        if isinstance(child, ast.FunctionDef)
                    ]
                    node_dict['bases'] = [
                        base.id for base in node.bases 
                        if isinstance(base, ast.Name)
                    ]
                
                nodes.append(node_dict)
        
        return nodes
    
    def _analyze_file(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze a single file."""
        functions = []
        classes = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or ""
                })
            elif isinstance(node, ast.ClassDef):
                classes[node.name] = {
                    'methods': [
                        child.name for child in node.body 
                        if isinstance(child, ast.FunctionDef)
                    ],
                    'docstring': ast.get_docstring(node) or "",
                    'base_classes': [
                        base.id for base in node.bases 
                        if isinstance(base, ast.Name)
                    ]
                }
        
        return {
            'language': '.py',
            'functions': functions,
            'classes': classes,
            'complexity': len(functions) + len(classes)
        }
    
    def _find_duplicates(self, nodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find duplicate code patterns."""
        duplicates = {}
        
        # Group nodes by type
        functions = [n for n in nodes if n['type'] == 'function']
        classes = [n for n in nodes if n['type'] == 'class']
        
        # Check function duplicates
        for i, func1 in enumerate(functions):
            for func2 in functions[i+1:]:
                if self._are_functions_similar(func1['source'], func2['source']):
                    if 'functions' not in duplicates:
                        duplicates['functions'] = []
                    
                    duplicates['functions'].append({
                        'file1': func1['file'],
                        'file2': func2['file'],
                        'function1': func1['name'],
                        'function2': func2['name'],
                        'similarity': self._calculate_similarity(
                            func1['source'], 
                            func2['source']
                        )
                    })
        
        # Check class duplicates
        for i, class1 in enumerate(classes):
            for class2 in classes[i+1:]:
                if self._are_classes_similar(class1, class2):
                    if 'classes' not in duplicates:
                        duplicates['classes'] = []
                    
                    duplicates['classes'].append({
                        'file1': class1['file'],
                        'file2': class2['file'],
                        'class1': class1['name'],
                        'class2': class2['name'],
                        'similarity': self._calculate_class_similarity(class1, class2)
                    })
        
        return duplicates
    
    def _are_functions_similar(self, source1: str, source2: str) -> bool:
        """Check if two functions are similar."""
        similarity = self._calculate_similarity(source1, source2)
        return similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, source1: str, source2: str) -> float:
        """Calculate similarity between two code snippets."""
        # Normalize whitespace
        source1 = ' '.join(source1.split())
        source2 = ' '.join(source2.split())
        
        # Simple similarity based on shared tokens
        tokens1 = set(source1.split())
        tokens2 = set(source2.split())
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _are_classes_similar(self, class1: Dict[str, Any], class2: Dict[str, Any]) -> bool:
        """Check if two classes are similar."""
        similarity = self._calculate_class_similarity(class1, class2)
        return similarity >= self.similarity_threshold
    
    def _calculate_class_similarity(self, class1: Dict[str, Any], class2: Dict[str, Any]) -> float:
        """Calculate similarity between two classes."""
        # Compare methods
        methods1 = set(class1['methods'])
        methods2 = set(class2['methods'])
        
        method_similarity = len(methods1 & methods2) / len(methods1 | methods2) if methods1 or methods2 else 0.0
        
        # Compare base classes
        bases1 = set(class1['bases'])
        bases2 = set(class2['bases'])
        
        base_similarity = len(bases1 & bases2) / len(bases1 | bases2) if bases1 or bases2 else 0.0
        
        # Weighted average
        return 0.7 * method_similarity + 0.3 * base_similarity
    
    def _analyze_architecture(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze architectural patterns."""
        issues = []
        
        # Check for circular dependencies
        # Check for deep inheritance
        # Check for large classes
        # Check for tight coupling
        
        return issues
    
    def _analyze_structure(self, nodes: List[ast.AST]) -> List[Dict[str, Any]]:
        """Analyze structural patterns."""
        insights = []
        
        # Analyze code organization
        # Check for design patterns
        # Identify anti-patterns
        
        return insights
    
    def _analyze_themes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze code themes."""
        themes = []
        
        # Identify common patterns
        # Group related functionality
        # Find architectural themes
        
        return themes
    
    def _find_top_violators(self, results: ScanResults) -> List[Dict[str, Any]]:
        """Find files with most duplicates."""
        file_counts = {}
        
        for category in results.duplicates.values():
            for item in category:
                file_counts[item['file1']] = file_counts.get(item['file1'], 0) + 1
                file_counts[item['file2']] = file_counts.get(item['file2'], 0) + 1
        
        return [
            {'file': file, 'count': count}
            for file, count in sorted(
                file_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
    
    def _generate_narrative(self, results: ScanResults) -> str:
        """Generate a narrative description of scan results."""
        narrative = ["Code Analysis Report"]
        
        # Add summary
        narrative.append(f"\nAnalyzed {results.total_files} files in {results.scan_time:.2f} seconds")
        narrative.append(f"Found {results.total_duplicates} instances of code duplication")
        
        # Add architectural issues
        if results.architectural_issues:
            narrative.append("\nArchitectural Issues:")
            for issue in results.architectural_issues:
                narrative.append(f"- {issue['description']}")
        
        # Add structural insights
        if results.structural_insights:
            narrative.append("\nStructural Insights:")
            for insight in results.structural_insights:
                narrative.append(f"- {insight['description']}")
        
        # Add themes
        if results.themes:
            narrative.append("\nCode Themes:")
            for theme in results.themes:
                narrative.append(f"- {theme['name']}: {theme['description']}")
        
        # Add top violators
        if results.top_violators:
            narrative.append("\nTop Duplicate Violators:")
            for violator in results.top_violators[:5]:
                narrative.append(f"- {violator['file']}: {violator['count']} duplicates")
        
        return "\n".join(narrative)
    
    def _generate_init_files(self) -> List[str]:
        """Generate __init__.py files for Python packages."""
        init_files = []
        
        # Find all directories that need __init__.py
        for path in self.project_root.rglob("*"):
            if path.is_dir() and not path.name.startswith("."):
                init_path = path / "__init__.py"
                if not init_path.exists():
                    try:
                        init_path.touch()
                        init_files.append(str(init_path.relative_to(self.project_root)))
                    except Exception as e:
                        self.logger.warning(f"Failed to create {init_path}: {e}")
        
        return init_files

async def main():
    """Main entry point for the scanner."""
    parser = argparse.ArgumentParser(description='Scan Python code for patterns and issues')
    parser.add_argument('project_root', help='Root directory of the project to scan')
    parser.add_argument('--output-dir', help='Directory to write reports to')
    parser.add_argument('--similarity-threshold', type=float, default=0.8,
                       help='Minimum similarity score (0-1) to consider code similar')
    parser.add_argument('--categorize-agents', action='store_true',
                       help='Categorize agents')
    parser.add_argument('--generate-init', action='store_true',
                       help='Generate __init__.py files')
    parser.add_argument('--safe-mode', action='store_true',
                       help='Use safe mode with strict path filtering')
    
    args = parser.parse_args()
    
    scanner = Scanner(
        args.project_root,
        args.output_dir,
        args.similarity_threshold,
        args.safe_mode
    )
    
    results = await scanner.scan(
        categorize_agents=args.categorize_agents,
        generate_init=args.generate_init
    )
    
    print(results.narrative)
    return 0

if __name__ == '__main__':
    asyncio.run(main())

