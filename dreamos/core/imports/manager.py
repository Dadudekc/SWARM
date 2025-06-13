"""
Dream.OS Import Manager

Core module for managing Python imports across the project.
"""

import ast
import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable

logger = logging.getLogger(__name__)

@dataclass
class ImportInfo:
    """Information about imports in a file."""
    file_path: Path
    standard_imports: List[Tuple[str, str]] = field(default_factory=list)  # (line, module)
    from_imports: List[Tuple[str, str, List[str]]] = field(default_factory=list)  # (line, module, names)
    relative_imports: List[Tuple[str, str]] = field(default_factory=list)  # (line, module)
    errors: List[str] = field(default_factory=list)

@dataclass
class ImportUpdateResults:
    """Results from an import update operation."""
    total_files: int = 0
    modified_files: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    backup_path: Optional[Path] = None
    test_results: Optional[Dict[str, Any]] = None

class ImportManager:
    """Core class for managing Python imports."""
    
    def __init__(self, project_dir: str, dry_run: bool = False,
                 progress_callback: Optional[Callable[[str, float], None]] = None):
        """Initialize the import manager.
        
        Args:
            project_dir: Path to project directory
            dry_run: Whether to perform a dry run without making changes
            progress_callback: Optional callback for progress updates
        """
        self.project_dir = Path(project_dir)
        self.dry_run = dry_run
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
    def _update_progress(self, message: str, progress: float):
        """Update progress if callback is provided."""
        if self.progress_callback:
            self.progress_callback(message, progress)
            
    def create_backup(self, backup_dir: Optional[str] = None) -> Optional[Path]:
        """Create a backup of the project directory.
        
        Args:
            backup_dir: Optional backup directory path
            
        Returns:
            Path to backup directory if successful, None otherwise
        """
        try:
            if backup_dir:
                backup_path = Path(backup_dir)
            else:
                backup_path = Path("backups") / f"import_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(self.project_dir, backup_path)
            self.logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
            
    def analyze_imports(self, file_path: Path) -> ImportInfo:
        """Analyze imports in a Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            ImportInfo object containing import analysis
        """
        info = ImportInfo(file_path=file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            tree = ast.parse(content)
            
            # Find all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        info.standard_imports.append((
                            ast.get_source_segment(content, node),
                            name.name
                        ))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    names = [n.name for n in node.names]
                    if node.level > 0:  # Relative import
                        info.relative_imports.append((
                            ast.get_source_segment(content, node),
                            '.' * node.level + module
                        ))
                    else:
                        info.from_imports.append((
                            ast.get_source_segment(content, node),
                            module,
                            names
                        ))
                        
        except Exception as e:
            error_msg = f"Failed to analyze imports in {file_path}: {e}"
            self.logger.error(error_msg)
            info.errors.append(error_msg)
            
        return info
        
    def update_imports(self, file_path: Path, move_map: Dict[str, str]) -> bool:
        """Update imports in a Python file based on the move map.
        
        Args:
            file_path: Path to Python file
            move_map: Dictionary mapping old module paths to new ones
            
        Returns:
            bool: True if file was modified
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            modified = False
            new_content = content
            
            # Update standard imports
            for old_path, new_path in move_map.items():
                old_module = old_path.replace('\\', '.').replace('/', '.')
                new_module = new_path.replace('\\', '.').replace('/', '.')
                
                # Handle both import styles
                patterns = [
                    (f'from {old_module} import', f'from {new_module} import'),
                    (f'import {old_module}', f'import {new_module}'),
                    (f'from {old_module}.', f'from {new_module}.'),
                    (f'import {old_module}.', f'import {new_module}.')
                ]
                
                for old_pattern, new_pattern in patterns:
                    if old_pattern in new_content:
                        new_content = new_content.replace(old_pattern, new_pattern)
                        modified = True
                        
            if modified and not self.dry_run:
                # Write updated content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                # Format the file
                self.format_file(file_path)
                
            return modified
            
        except Exception as e:
            self.logger.error(f"Failed to update imports in {file_path}: {e}")
            return False
            
    def format_file(self, file_path: Path) -> None:
        """Format a Python file using black and isort.
        
        Args:
            file_path: Path to Python file
        """
        if self.dry_run:
            self.logger.info(f"Would format {file_path}")
            return
            
        try:
            # Run isort
            subprocess.run(["isort", str(file_path)], check=True)
            # Run black
            subprocess.run(["black", str(file_path)], check=True)
            self.logger.info(f"Formatted {file_path}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to format {file_path}: {e}")
            
    def run_tests(self) -> Dict[str, Any]:
        """Run tests to verify changes.
        
        Returns:
            Dictionary containing test results
        """
        if self.dry_run:
            self.logger.info("Would run tests")
            return {"status": "skipped", "reason": "dry_run"}
            
        try:
            result = subprocess.run(
                ["pytest", "tests/", "--maxfail=10", "-v"],
                capture_output=True,
                text=True
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failure",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run tests: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def update_project_imports(self, move_map: Dict[str, str],
                                   backup: bool = True) -> ImportUpdateResults:
        """Update imports across the entire project.
        
        Args:
            move_map: Dictionary mapping old module paths to new ones
            backup: Whether to create a backup before making changes
            
        Returns:
            ImportUpdateResults object containing update results
        """
        results = ImportUpdateResults()
        
        try:
            # Create backup if requested
            if backup and not self.dry_run:
                results.backup_path = self.create_backup()
                if not results.backup_path:
                    raise Exception("Failed to create backup")
                    
            # Find all Python files
            python_files = []
            for root, _, files in os.walk(self.project_dir):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)
                        
            results.total_files = len(python_files)
            self.logger.info(f"Found {results.total_files} Python files")
            
            # Update imports
            for i, file_path in enumerate(python_files):
                try:
                    if self.update_imports(file_path, move_map):
                        results.modified_files += 1
                        self.logger.info(f"Modified {file_path}")
                except Exception as e:
                    results.errors.append({
                        "file": str(file_path),
                        "error": str(e)
                    })
                    
                # Update progress
                progress = (i + 1) / len(python_files)
                self._update_progress(f"Updating imports ({i+1}/{len(python_files)})", progress)
                
            # Run tests
            results.test_results = self.run_tests()
            
            if results.test_results["status"] != "success":
                self.logger.error("Tests failed after import updates")
                if results.backup_path:
                    self.logger.info("Restoring from backup...")
                    try:
                        shutil.rmtree(self.project_dir)
                        shutil.copytree(results.backup_path, self.project_dir)
                        self.logger.info("Restored from backup successfully")
                    except Exception as e:
                        self.logger.error(f"Failed to restore from backup: {e}")
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to update project imports: {e}")
            results.errors.append({
                "file": "project",
                "error": str(e)
            })
            return results 