import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
import os
import ast
import fnmatch
import chardet
from concurrent.futures import ThreadPoolExecutor
import argparse

from .models.analysis import FileAnalysis, ProjectAnalysis, ClassInfo
from .analyzers.dependency_analyzer import DependencyAnalyzer
from .analyzers.quality_analyzer import QualityAnalyzer
from .analyzers.ast_analyzer import ASTAnalyzer
from .utils.file_utils import is_test_file

logger = logging.getLogger(__name__)

class PathEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Path objects."""
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

class Scanner:
    """Main scanner class that orchestrates the analysis process."""
    
    def __init__(self, project_root: str, output_path: Optional[str] = None, max_workers: int = None):
        self.project_root = Path(project_root).resolve()
        self.output_path = Path(output_path).resolve() if output_path else self.project_root
        self.dependency_analyzer = DependencyAnalyzer(self.project_root)
        self.quality_analyzer = QualityAnalyzer()
        self.ast_analyzer = ASTAnalyzer()
        self.max_workers = max_workers or (os.cpu_count() or 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
    async def scan_project(self, ignore_patterns: Optional[List[str]] = None) -> ProjectAnalysis:
        """Scan the project and generate analysis results."""
        errors = []
        skipped_files = []
        
        try:
            # Find all valid files
            valid_files = self._find_valid_files(ignore_patterns)
            logger.info(f"Found {len(valid_files)} valid files for analysis")
            
            # Process files asynchronously with batching
            logger.info("Processing files asynchronously...")
            batch_size = 50  # Process files in batches to manage memory
            files: Dict[str, FileAnalysis] = {}
            test_files: Dict[str, FileAnalysis] = {}
            
            for i in range(0, len(valid_files), batch_size):
                batch = valid_files[i:i + batch_size]
                tasks = []
                for file_path in batch:
                    task = asyncio.create_task(self._process_file(file_path))
                    tasks.append(task)
                
                # Wait for batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process batch results
                for result in results:
                    if isinstance(result, Exception):
                        error_msg = f"Error processing file: {str(result)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
                        
                    if result:
                        file_path, analysis = result
                        if is_test_file(file_path):
                            test_files[str(file_path)] = analysis
                        else:
                            files[str(file_path)] = analysis
            
            # Analyze dependencies
            dependencies, circular_deps = self.dependency_analyzer.analyze_dependencies(files)
            
            # Identify core and peripheral components
            core_components, peripheral_components = self.dependency_analyzer.identify_core_components(
                files, dependencies
            )
            
            # Group files into modules
            modules = self.dependency_analyzer.group_into_modules(files)
            
            # Calculate quality metrics
            total_complexity = sum(file.complexity for file in files.values())
            total_duplication = sum(file.duplicate_lines for file in files.values())
            
            # Calculate test coverage
            coverage = self.quality_analyzer.analyze_test_coverage(test_files, files)
            average_coverage = sum(coverage.values()) / len(coverage) if coverage else 0.0
            
            # Create project analysis
            analysis = ProjectAnalysis(
                project_root=Path(self.project_root).absolute(),
                scan_time=datetime.now(),
                files=files,
                dependencies=dependencies,
                circular_dependencies=circular_deps,
                modules=modules,
                core_components=core_components,
                peripheral_components=peripheral_components,
                test_files=test_files,
                total_complexity=total_complexity,
                total_duplication=total_duplication,
                average_test_coverage=average_coverage,
                errors=errors,
                skipped_files=skipped_files
            )
            
            # Save results
            self._save_results(analysis)
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error scanning project: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            raise
        
    def _find_valid_files(self, ignore_patterns: Optional[List[str]] = None) -> List[Path]:
        """Find all valid files in the project."""
        valid_files = []
        file_extensions = {'.py', '.rs', '.js', '.ts'}
        
        # Default ignore patterns for Dream.OS
        default_ignore = [
            # Python specific
            '*.pyc',
            '__pycache__/*',
            '*.egg-info/*',
            '*.egg/*',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            
            # Virtual environments
            '.venv/*',
            'venv/*',
            'env/*',
            '.env/*',
            'virtualenv/*',
            
            # Node.js
            'node_modules/*',
            'package-lock.json',
            'yarn.lock',
            
            # Version control
            '.git/*',
            '.svn/*',
            '.hg/*',
            
            # Build artifacts
            'build/*',
            'dist/*',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            
            # IDE and editor files
            '.idea/*',
            '.vscode/*',
            '*.swp',
            '*.swo',
            '*~',
            
            # Documentation
            'docs/_build/*',
            'docs/api/*',
            
            # Test coverage
            '.coverage',
            'htmlcov/*',
            'coverage.xml',
            
            # Logs and databases
            '*.log',
            '*.sqlite',
            '*.db',
            
            # Temporary files
            '*.tmp',
            '*.temp',
            '*.bak',
            
            # Dream.OS specific
            'runtime/*',
            'logs/*',
            'temp/*',
            'cache/*',
            'data/*',
            'uploads/*',
            'downloads/*',
            'backups/*',
            '*.bak',
            '*.old',
            '*.orig',
            '*.rej',
            '*.swp',
            '*.swo',
            '*~'
        ]
        
        # Combine default and user ignore patterns
        all_ignore_patterns = default_ignore + (ignore_patterns or [])
        
        # Focus on core project directories
        core_dirs = [
            'dreamos/core',
            'dreamos/agents',
            'dreamos/utils',
            'agent_tools',
            'tests'
        ]
        
        try:
            for root, dirs, files in os.walk(self.project_root):
                root_path = Path(root).resolve()
                rel_root = root_path.relative_to(self.project_root)
                
                # Skip if not in core directories
                if not any(str(rel_root).startswith(core_dir) for core_dir in core_dirs):
                    continue
                
                # Skip ignored directories
                if any(fnmatch.fnmatch(str(rel_root), pattern) for pattern in all_ignore_patterns):
                    continue
                    
                for file in files:
                    file_path = (root_path / file).resolve()
                    rel_path = file_path.relative_to(self.project_root)
                    
                    # Skip ignored files
                    if any(fnmatch.fnmatch(str(rel_path), pattern) for pattern in all_ignore_patterns):
                        continue
                        
                    if file_path.suffix.lower() in file_extensions:
                        valid_files.append(file_path)
                        
            logger.info(f"Found {len(valid_files)} valid files in core project directories")
            return valid_files
            
        except Exception as e:
            logger.error(f"Error finding valid files: {e}")
            raise
        
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding using chardet."""
        try:
            with file_path.open('rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception as e:
            logger.warning(f"Error detecting encoding for {file_path}: {e}")
            return 'utf-8'
        
    async def _process_file(self, file_path: Path) -> Optional[Tuple[Path, FileAnalysis]]:
        """Process a single file and return its analysis."""
        try:
            # Detect file encoding
            encoding = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool, self._detect_encoding, file_path
            )
            
            # Read file content
            try:
                with file_path.open('r', encoding=encoding) as f:
                    source_code = f.read()
            except UnicodeDecodeError:
                # Fallback to utf-8 with error handling
                with file_path.open('r', encoding='utf-8', errors='replace') as f:
                    source_code = f.read()
                
            # Skip JavaScript files for now as they require different parsing
            if file_path.suffix.lower() in {'.js', '.ts'}:
                logger.info(f"Skipping JavaScript/TypeScript file: {file_path}")
                return None
                
            # Analyze AST
            functions, classes = self.ast_analyzer.analyze(source_code)
            
            # Calculate complexity and duplication
            complexity, duplicate_lines = self.quality_analyzer.analyze_file_quality(
                file_path, source_code
            )
            
            # Extract dependencies
            imports = self.dependency_analyzer.analyze_file_dependencies(file_path, source_code)
            
            # Create file analysis
            analysis = FileAnalysis(
                path=file_path,
                language=file_path.suffix,
                functions=functions,
                classes=classes,
                routes=[],  # TODO: Add route detection
                complexity=complexity,
                dependencies=set(),
                imports=imports,
                test_coverage=0.0,
                cyclomatic_complexity=complexity,
                duplicate_lines=duplicate_lines
            )
            
            return file_path, analysis
            
        except SyntaxError as e:
            error_msg = f"Syntax error in {file_path}: {e}"
            logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg)
            return None
            
    def _save_results(self, analysis: ProjectAnalysis):
        """Save analysis results to files."""
        try:
            # Create output directory if it doesn't exist
            self.output_path.mkdir(parents=True, exist_ok=True)
            
            # Save main analysis
            analysis_path = self.output_path / "project_analysis.json"
            with analysis_path.open('w', encoding='utf-8') as f:
                json.dump(analysis.to_dict(), f, indent=4, cls=PathEncoder)
            logger.info(f"✅ Project analysis saved to {analysis_path}")
            
            # Save test analysis
            test_analysis = {
                "project_root": str(self.project_root),
                "scan_time": analysis.scan_time.isoformat(),
                "test_files": {
                    str(path): file.to_dict() for path, file in analysis.test_files.items()
                }
            }
            test_analysis_path = self.output_path / "test_analysis.json"
            with test_analysis_path.open('w', encoding='utf-8') as f:
                json.dump(test_analysis, f, indent=4, cls=PathEncoder)
            logger.info(f"✅ Test analysis saved to {test_analysis_path}")
            
            # Save ChatGPT context
            context = {
                "project_root": str(self.project_root),
                "scan_time": analysis.scan_time.isoformat(),
                "num_files_analyzed": len(analysis.files),
                "analysis_details": analysis.to_dict(),
                "dependencies": {
                    str(k): list(v) for k, v in analysis.dependencies.items()
                },
                "circular_dependencies": [
                    list(dep_set) for dep_set in analysis.circular_dependencies
                ],
                "modules": {
                    k: list(v) for k, v in analysis.modules.items()
                },
                "core_components": list(analysis.core_components),
                "peripheral_components": list(analysis.peripheral_components),
                "quality_metrics": {
                    "total_complexity": analysis.total_complexity,
                    "total_duplication": analysis.total_duplication,
                    "average_test_coverage": analysis.average_test_coverage
                },
                "errors": analysis.errors,
                "skipped_files": analysis.skipped_files
            }
            context_path = self.output_path / "chatgpt_project_context.json"
            with context_path.open('w', encoding='utf-8') as f:
                json.dump(context, f, indent=4, cls=PathEncoder)
            logger.info(f"✅ ChatGPT context saved to {context_path}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Scan a project and generate analysis results")
    parser.add_argument("--project-root", required=True, help="Root directory of the project to scan")
    parser.add_argument("--output", required=True, help="Directory to save analysis results")
    parser.add_argument("--max-workers", type=int, help="Maximum number of worker threads")
    parser.add_argument("--ignore", nargs="*", help="Patterns to ignore (e.g., '*.pyc', 'tests/*')")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create scanner instance
    scanner = Scanner(
        project_root=args.project_root,
        output_path=args.output,
        max_workers=args.max_workers
    )
    
    # Run scan
    try:
        asyncio.run(scanner.scan_project(ignore_patterns=args.ignore))
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        raise
