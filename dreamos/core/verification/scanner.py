"""
Dream.OS Code Scanner

Analyzes code for duplicates, similar patterns, and provides detailed reports.
"""

import ast
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Callable
import asyncio
from datetime import datetime
from tqdm import tqdm

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
    empty_dirs: List[str] = field(default_factory=list)
    duplicate_files: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def summary(self) -> Dict[str, Any]:
        """Generate a summary of scan results."""
        return {
            "type": "scan_summary",
            "total_files": self.total_files,
            "total_duplicates": self.total_duplicates,
            "scan_time": self.scan_time,
            "top_violators": self.top_violators,
            "empty_dirs": len(self.empty_dirs),
            "duplicate_files": len(self.duplicate_files),
            "errors": len(self.errors)
        }
    
    def format_full_report(self) -> str:
        """Format a human-readable report."""
        report = [
            "Scan Summary",
            "===========",
            f"Total Files: {self.total_files}",
            f"Total Duplicates: {self.total_duplicates}",
            f"Scan Time: {self.scan_time:.2f}s",
            f"Errors: {len(self.errors)}",
            "\nTop Violators:",
        ]
        
        for violator in self.top_violators:
            report.append(f"- {violator['file']}: {violator['count']} duplicates")
            
        if self.duplicate_files:
            report.append("\nDuplicate Files:")
            for name, files in self.duplicate_files.items():
                report.append(f"\n{name}:")
                for f in files:
                    report.append(f"  - {f}")
                    
        if self.empty_dirs:
            report.append("\nEmpty Directories:")
            for d in self.empty_dirs:
                report.append(f"  - {d}")
                
        if self.errors:
            report.append("\nErrors:")
            for error in self.errors:
                report.append(f"  - {error['file']}: {error['error']}")
            
        report.append("\nDetailed Findings:")
        report.append(self.narrative)
        
        return "\n".join(report)
    
    def save_reports(self, output_dir: Optional[str] = None) -> bool:
        """Save scan results to files.
        
        Args:
            output_dir: Optional output directory
            
        Returns:
            bool: True if reports were saved successfully
        """
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
                "empty_dirs": self.empty_dirs,
                "duplicate_files": self.duplicate_files,
                "errors": self.errors
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
                "scan_time": self.scan_time,
                "empty_dirs": self.empty_dirs,
                "duplicate_files": self.duplicate_files,
                "errors": self.errors
            }
            
            with open(output_path / "chatgpt_project_context.json", 'w') as f:
                json.dump(chatgpt_context, f, indent=4)
            
            # Save human-readable report
            with open(output_path / "scan_report.txt", 'w') as f:
                f.write(self.format_full_report())
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving reports: {str(e)}")
            return False

class Scanner:
    """Code scanner for detecting duplicates and similar patterns."""
    
    def __init__(self, project_dir: str, similarity_threshold: float = 0.8, 
                 progress_callback: Optional[Callable[[str, float], None]] = None):
        """Initialize scanner.
        
        Args:
            project_dir: Path to project directory
            similarity_threshold: Threshold for considering code similar (0-1)
            progress_callback: Optional callback for progress updates
        """
        self.project_dir = Path(project_dir)
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback
        
    def _update_progress(self, message: str, progress: float):
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(message, progress)
        
    async def scan_project(self, categorize_agents: bool = False, generate_init: bool = False) -> ScanResults:
        """Scan the project for duplicates and similar patterns.
        
        Args:
            categorize_agents: Whether to categorize agent types
            generate_init: Whether to generate __init__.py files
            
        Returns:
            ScanResults object containing scan results
        """
        start_time = datetime.now()
        results = ScanResults()
        
        try:
            # Get all Python files
            self._update_progress("Finding Python files...", 0.1)
            python_files = list(self.project_dir.rglob("*.py"))
            results.total_files = len(python_files)
            
            # Skip test files and __init__.py
            python_files = [
                f for f in python_files 
                if not f.name.startswith("test_") 
                and f.name != "__init__.py"
            ]
            
            # Find duplicate files
            self._update_progress("Finding duplicate files...", 0.2)
            results.duplicate_files = self._find_duplicate_files()
            
            # Find empty directories
            self._update_progress("Finding empty directories...", 0.3)
            results.empty_dirs = self._find_empty_dirs()
            
            # Analyze each file
            self._update_progress("Analyzing files...", 0.4)
            for i, file_path in enumerate(tqdm(python_files, desc="Analyzing files")):
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
                    error_msg = f"Error analyzing {file_path}: {str(e)}"
                    self.logger.warning(error_msg)
                    results.errors.append({
                        'file': str(file_path),
                        'error': str(e)
                    })
                    continue
                
                # Update progress
                progress = 0.4 + (0.4 * (i + 1) / len(python_files))
                self._update_progress(f"Analyzing file {i+1}/{len(python_files)}...", progress)
            
            # Generate narrative
            self._update_progress("Generating report...", 0.9)
            results.narrative = self._generate_narrative(results)
            
            # Find top violators
            results.top_violators = self._find_top_violators(results)
            
            # Calculate scan time
            results.scan_time = (datetime.now() - start_time).total_seconds()
            
            self._update_progress("Scan complete!", 1.0)
            return results
            
        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            self.logger.error(error_msg)
            results.errors.append({
                'file': 'scanner',
                'error': str(e)
            })
            return results
            
    def _find_duplicate_files(self) -> Dict[str, List[str]]:
        """Find files with duplicate names.
        
        Returns:
            Dictionary mapping filenames to lists of file paths
        """
        by_name = defaultdict(list)
        
        # Find all Python files
        for f in self.project_dir.rglob('*.py'):
            by_name[f.name].append(str(f))
            
        # Filter to only include duplicates
        return {
            name: files 
            for name, files in by_name.items() 
            if len(files) > 1
        }
        
    def _find_empty_dirs(self) -> List[str]:
        """Find empty directories.
        
        Returns:
            List of empty directory paths
        """
        empty_dirs = []
        
        for root, dirs, files in os.walk(self.project_dir):
            if not dirs and not files and root != str(self.project_dir):
                empty_dirs.append(root)
                
        return empty_dirs
    
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
            
        narrative.append(f"\nFound {results.total_duplicates} duplicate code blocks across {results.total_files} files.")
        
        if results.duplicates.get('functions'):
            narrative.append("\nFunction Duplicates:")
            for dup in results.duplicates['functions']:
                narrative.append(
                    f"- {dup['function1']} in {dup['file1']} "
                    f"is {dup['similarity']:.0%} similar to "
                    f"{dup['function2']} in {dup['file2']}"
                )
                
        if results.duplicate_files:
            narrative.append("\nDuplicate Files:")
            for name, files in results.duplicate_files.items():
                narrative.append(f"\n{name}:")
                for f in files:
                    narrative.append(f"  - {f}")
                    
        if results.empty_dirs:
            narrative.append("\nEmpty Directories:")
            for d in results.empty_dirs:
                narrative.append(f"  - {d}")
                
        return "\n".join(narrative)
    
    def _find_top_violators(self, results: ScanResults) -> List[Dict[str, Any]]:
        """Find files with the most duplicates.
        
        Args:
            results: Scan results
            
        Returns:
            List of top violators with counts
        """
        violators = defaultdict(int)
        
        # Count duplicates per file
        for dup_type, dups in results.duplicates.items():
            for dup in dups:
                violators[dup['file1']] += 1
                violators[dup['file2']] += 1
                
        # Convert to list and sort
        violator_list = [
            {'file': f, 'count': c}
            for f, c in violators.items()
        ]
        
        return sorted(violator_list, key=lambda x: x['count'], reverse=True) 