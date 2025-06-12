#!/usr/bin/env python3
"""
Standalone code scanner for Dream.OS.
Analyzes code for duplicates and generates reports.
"""

import ast
import json
import logging
import sys
import argparse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

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
                "analysis_details": self.project_analysis
            }
            
            with open(output_path / "project_analysis.json", 'w') as f:
                json.dump(project_analysis, f, indent=4)
            
            # Save ChatGPT context
            chatgpt_context = {
                "project_root": str(Path.cwd()),
                "num_files_analyzed": self.total_files,
                "analysis_details": self.project_analysis,
                "duplicates": self.duplicates,
                "top_violators": self.top_violators,
                "scan_time": self.scan_time
            }
            
            with open(output_path / "chatgpt_project_context.json", 'w') as f:
                json.dump(chatgpt_context, f, indent=4)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving reports: {str(e)}")
            return False

class Scanner:
    """Code scanner for detecting duplicates and similar patterns."""
    
    def __init__(self, project_dir: str, similarity_threshold: float = 0.8):
        """Initialize scanner."""
        self.project_dir = Path(project_dir)
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        
    def scan_project(self) -> ScanResults:
        """Scan the project for duplicates and similar patterns."""
        start_time = datetime.now()
        results = ScanResults()
        
        try:
            # Get all Python files
            python_files = list(self.project_dir.rglob("*.py"))
            results.total_files = len(python_files)
            
            # Skip test files, __init__.py, and virtual environment
            python_files = [
                f for f in python_files 
                if not f.name.startswith("test_") 
                and f.name != "__init__.py"
                and ".venv" not in str(f)
            ]
            
            # Analyze each file
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Find functions and classes
                    functions = []
                    classes = {}
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Get function source
                            func_source = ast.get_source_segment(content, node)
                            if func_source:
                                functions.append({
                                    'name': node.name,
                                    'source': func_source,
                                    'file': str(file_path)
                                })
                        elif isinstance(node, ast.ClassDef):
                            # Get class methods
                            methods = []
                            for child in node.body:
                                if isinstance(child, ast.FunctionDef):
                                    methods.append(child.name)
                            
                            classes[node.name] = {
                                'methods': methods,
                                'docstring': ast.get_docstring(node) or "",
                                'base_classes': [base.id for base in node.bases if isinstance(base, ast.Name)],
                                'maturity': "Core Asset",
                                'agent_type': "Utility"
                            }
                    
                    # Add to project analysis
                    results.project_analysis[str(file_path)] = {
                        'language': '.py',
                        'functions': [f['name'] for f in functions],
                        'classes': classes,
                        'routes': [],
                        'complexity': len(functions) + len(classes)
                    }
                    
                    # Check for duplicates
                    for i, func1 in enumerate(functions):
                        for func2 in functions[i+1:]:
                            if self._are_functions_similar(func1['source'], func2['source']):
                                # Add to duplicates
                                if 'functions' not in results.duplicates:
                                    results.duplicates['functions'] = []
                                    
                                results.duplicates['functions'].append({
                                    'file1': func1['file'],
                                    'file2': func2['file'],
                                    'function1': func1['name'],
                                    'function2': func2['name'],
                                    'similarity': self._calculate_similarity(
                                        func1['source'], 
                                        func2['source']
                                    )
                                })
                                results.total_duplicates += 1
                
                except Exception as e:
                    self.logger.warning(f"Error analyzing {file_path}: {str(e)}")
                    continue
            
            # Generate narrative
            results.narrative = self._generate_narrative(results)
            
            # Find top violators
            results.top_violators = self._find_top_violators(results)
            
            # Calculate scan time
            results.scan_time = (datetime.now() - start_time).total_seconds()
            
            # Save reports
            results.save_reports()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Scan failed: {str(e)}")
            raise
    
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
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_narrative(self, results: ScanResults) -> str:
        """Generate a narrative description of scan results."""
        narrative = ["Code Duplication Analysis"]
        
        if results.total_duplicates == 0:
            narrative.append("No code duplication found.")
            return "\n".join(narrative)
            
        narrative.append(f"\nFound {results.total_duplicates} instances of code duplication.")
        
        if 'functions' in results.duplicates:
            narrative.append("\nFunction Duplicates:")
            for dup in results.duplicates['functions']:
                narrative.append(
                    f"- {dup['function1']} in {dup['file1']} "
                    f"similar to {dup['function2']} in {dup['file2']} "
                    f"(similarity: {dup['similarity']:.2f})"
                )
        
        return "\n".join(narrative)
    
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

def main():
    """Run the scanner on the project."""
    parser = argparse.ArgumentParser(description="Dream.OS Code Scanner")
    parser.add_argument("project_dir", nargs="?", default=".", help="Project directory to scan")
    parser.add_argument("--fail-on", choices=["duplicates", "complexity", "docs"], help="Exit with error if condition met")
    args = parser.parse_args()
    
    try:
        # Create scanner instance
        scanner = Scanner(args.project_dir)
        
        # Run scan
        results = scanner.scan_project()
        
        # Print summary
        print("\nScan Summary:")
        print(f"Total Files: {results.total_files}")
        print(f"Total Duplicates: {results.total_duplicates}")
        print(f"Scan Time: {results.scan_time:.2f}s")
        
        if results.top_violators:
            print("\nTop Violators:")
            for violator in results.top_violators:
                print(f"- {violator['file']}: {violator['count']} duplicates")
        
        print("\nDetailed findings saved to reports/")
        
        # Check fail conditions
        if args.fail_on == "duplicates" and results.total_duplicates > 0:
            print("\n❌ Duplicates detected - failing")
            sys.exit(1)
            
        if args.fail_on == "complexity":
            high_complex = {
                k: v for k, v in results.project_analysis.items() 
                if v.get('complexity', 0) > 15
            }
            if high_complex:
                print("\n❌ High complexity files detected:")
                for file, info in high_complex.items():
                    print(f"- {file}: {info['complexity']} complexity")
                sys.exit(1)
                
        if args.fail_on == "docs":
            # Check for duplicate docstrings
            docstrings = {}
            for file, info in results.project_analysis.items():
                for class_name, class_info in info.get('classes', {}).items():
                    if class_info.get('docstring'):
                        if class_info['docstring'] not in docstrings:
                            docstrings[class_info['docstring']] = []
                        docstrings[class_info['docstring']].append(f"{file}:{class_name}")
            
            duplicates = {doc: files for doc, files in docstrings.items() if len(files) > 1}
            if duplicates:
                print("\n❌ Duplicate docstrings detected:")
                for doc, files in duplicates.items():
                    print(f"\nDocstring: {doc[:100]}...")
                    for file in files:
                        print(f"- {file}")
                sys.exit(1)
        
    except Exception as e:
        print(f"Error running scanner: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 