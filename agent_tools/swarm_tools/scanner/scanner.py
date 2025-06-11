"""
Scanner Module
------------
Main module for scanning and analyzing code.
"""

import time
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .core.scan_results import ScanResults
from .analyzers.code_analyzer import CodeAnalyzer
from .analyzers.architecture_analyzer import ArchitectureAnalyzer
from .analyzers.agent_analyzer import AgentAnalyzer
from .analyzers.structure_analyzer import StructureAnalyzer
from .analyzers.theme_analyzer import ThemeAnalyzer
from .core.file_manager import FileManager
from .core.narrative import NarrativeGenerator
from .core.report_manager import ReportManager
from .reporters.reporter_factory import ReporterFactory

logger = logging.getLogger(__name__)

class Scanner:
    """Main scanner class for code analysis."""
    
    def __init__(self, project_root: str, output_dir: Optional[str] = None, safe_mode: bool = True):
        """Initialize the scanner.
        
        Args:
            project_root: Root directory of the project to scan
            output_dir: Directory to write reports to (defaults to project_root/reports)
            safe_mode: Whether to use safe mode with strict path filtering
        """
        self.project_root = Path(project_root)
        if output_dir is None:
            output_dir = self.project_root / 'reports'
        self.output_dir = Path(output_dir)
        
        # Initialize components
        self.file_manager = FileManager(self.project_root, safe_mode=safe_mode)
        self.report_manager = ReportManager(self.output_dir)
        self.analyzer = CodeAnalyzer()
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.agent_analyzer = AgentAnalyzer()
        self.structure_analyzer = StructureAnalyzer()
        self.theme_analyzer = ThemeAnalyzer()
        self.reporter_factory = ReporterFactory()
        
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
        
        # Find all Python files
        python_files = self.file_manager.find_python_files()
        
        # Generate __init__.py files if requested
        if generate_init:
            results.init_files = self.file_manager.generate_init_files()
            # Add generated __init__.py files to the count
            for init_file in results.init_files:
                init_path = self.project_root / init_file
                if init_path not in python_files:
                    python_files.append(init_path)
                    
        results.total_files = len(python_files)
        
        # Analyze each file
        all_node_dicts = []
        all_ast_nodes = []
        for file_path in python_files:
            node_dicts = self.analyzer.analyze_file(file_path)
            all_node_dicts.extend(node_dicts)
            all_ast_nodes.extend([d['ast_node'] for d in node_dicts if 'ast_node' in d])
            
        # Find duplicates
        duplicates = self.analyzer.find_duplicates(all_node_dicts)
        results.duplicates = duplicates
        results.total_duplicates = len(duplicates)
        
        # Analyze architectural issues
        results.architectural_issues = self.architecture_analyzer.analyze(all_node_dicts)
        
        # Categorize agents if requested
        if categorize_agents:
            results.agent_categories = self.agent_analyzer.analyze(all_node_dicts)
            
        # Analyze structural patterns (pass only AST nodes)
        results.structural_insights = self.structure_analyzer.analyze(all_ast_nodes)
        
        # Analyze themes
        results.themes = self.theme_analyzer.analyze(all_node_dicts)
        
        # Generate narrative
        results.narrative = NarrativeGenerator.generate(results)
        
        # Record scan time
        results.scan_time = time.time() - start_time
        
        return results
        
    def save_results(self, results: Any) -> bool:
        """Save scan results.
        
        Args:
            results: ScanResults object or dictionary
            
        Returns:
            True if results were saved successfully
        """
        try:
            # Create reports directory
            reports_dir = self.project_root / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert ScanResults to dict if needed
            if hasattr(results, 'summary'):
                results_dict = results.summary()
            elif hasattr(results, '__dict__'):
                results_dict = dict(results.__dict__)
            else:
                results_dict = results
            
            # Save JSON report
            json_reporter = self.reporter_factory.create_reporter('json', reports_dir)
            json_reporter.save_results(results_dict)
            
            # Save HTML report
            html_reporter = self.reporter_factory.create_reporter('html', reports_dir)
            html_reporter.save_results(results_dict)
            
            # Save text report
            text_reporter = self.reporter_factory.create_reporter('text', reports_dir)
            text_reporter.save_results(results_dict)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save scan results: {str(e)}")
            return False

async def main():
    """Main entry point for the scanner."""
    parser = argparse.ArgumentParser(description='Scan Python code for patterns and issues')
    parser.add_argument('project_root', help='Root directory of the project to scan')
    parser.add_argument('--output-dir', help='Directory to write reports to')
    parser.add_argument('--categorize-agents', action='store_true', help='Categorize agents')
    parser.add_argument('--generate-init', action='store_true', help='Generate __init__.py files')
    
    args = parser.parse_args()
    
    scanner = Scanner(args.project_root, args.output_dir)
    results = await scanner.scan(
        categorize_agents=args.categorize_agents,
        generate_init=args.generate_init
    )
    
    if scanner.save_results(results):
        print("Scan completed successfully")
        print(results.narrative)
    else:
        print("Error saving scan results")
        return 1
        
    return 0

if __name__ == '__main__':
    asyncio.run(main())

