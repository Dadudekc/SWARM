"""
Dream.OS Code Scanner

Analyzes code for duplicates, similar patterns, and provides detailed reports.
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import asyncio
from datetime import datetime

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
    
    def summary(self) -> Dict[str, Any]:
        """Generate a summary of scan results."""
        return {
            "type": "scan_summary",
            "total_files": self.total_files,
            "total_duplicates": self.total_duplicates,
            "scan_time": self.scan_time,
            "top_violators": self.top_violators
        }
    
    def format_full_report(self) -> str:
        """Format a human-readable report."""
        report = [
            "Scan Summary",
            "===========",
            f"Total Files: {self.total_files}",
            f"Total Duplicates: {self.total_duplicates}",
            f"Scan Time: {self.scan_time:.2f}s",
            "\nTop Violators:",
        ]
        
        for violator in self.top_violators:
            report.append(f"- {violator['file']}: {violator['count']} duplicates")
            
        report.append("\nDetailed Findings:")
        report.append(self.narrative)
        
        return "\n".join(report)

class Scanner:
    """Code scanner for detecting duplicates and similar patterns."""
    
    def __init__(self, project_dir: str, similarity_threshold: float = 0.8):
        """Initialize scanner.
        
        Args:
            project_dir: Path to project directory
            similarity_threshold: Threshold for considering code similar (0-1)
        """
        self.project_dir = Path(project_dir)
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        
    async def scan_project(self) -> ScanResults:
        """Scan the project for duplicates and similar patterns."""
        start_time = datetime.now()
        results = ScanResults()
        
        try:
            # Get all Python files
            python_files = list(self.project_dir.rglob("*.py"))
            results.total_files = len(python_files)
            
            # Skip test files and __init__.py
            python_files = [
                f for f in python_files 
                if not f.name.startswith("test_") 
                and f.name != "__init__.py"
            ]
            
            # Analyze each file
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Find functions
                    functions = []
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