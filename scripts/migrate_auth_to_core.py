#!/usr/bin/env python3
"""
Auth System Migration Script

Moves the authentication system from src/auth/ to dreamos/core/auth/
with proper import updates and validation.
"""

import os
import shutil
import logging
from pathlib import Path
import re
from datetime import datetime
import subprocess
from typing import List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuthMigration:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.src_auth = self.root_dir / 'src' / 'auth'
        self.target_auth = self.root_dir / 'dreamos' / 'core' / 'auth'
        self.backup_dir = self.root_dir / 'backups' / f'auth_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.updated_files: Set[Path] = set()
        
    def validate_environment(self) -> bool:
        """Validate the environment before migration."""
        try:
            # Check if src/auth exists
            if not self.src_auth.exists():
                logger.error(f"Source directory {self.src_auth} does not exist")
                return False
                
            # Create target directory if it doesn't exist
            self.target_auth.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if target directory is empty
            if self.target_auth.exists() and any(self.target_auth.iterdir()):
                logger.warning(f"Target directory {self.target_auth} is not empty")
                return False
                
            # Create target directory
            self.target_auth.mkdir(exist_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
            
    def create_backup(self) -> bool:
        """Create backup of auth system."""
        try:
            self.backup_dir.mkdir(parents=True)
            shutil.copytree(self.src_auth, self.backup_dir / 'auth')
            logger.info(f"Created backup at {self.backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
            
    def find_import_references(self) -> List[Path]:
        """Find all files that import from dreamos.core.auth."""
        import_pattern = re.compile(r'from\s+src\.auth|import\s+src\.auth')
        files_with_imports = []
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if import_pattern.search(content):
                                files_with_imports.append(file_path)
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        
        return files_with_imports
        
    def update_imports(self, files: List[Path]) -> bool:
        """Update import statements in files."""
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Update imports
                new_content = content.replace('from dreamos.core.auth', 'from dreamos.core.auth')
                new_content = new_content.replace('import dreamos.core.auth', 'import dreamos.core.auth')
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.updated_files.add(file_path)
                    logger.info(f"Updated imports in {file_path}")
                    
            except Exception as e:
                logger.error(f"Failed to update imports in {file_path}: {e}")
                return False
                
        return True
        
    def migrate_files(self) -> bool:
        """Move auth files to new location."""
        try:
            # Create target directory
            self.target_auth.mkdir(parents=True, exist_ok=True)
            
            # Copy files individually
            for item in self.src_auth.iterdir():
                dest = self.target_auth / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                    logger.info(f"Copied {item} to {dest}")
                elif item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                    logger.info(f"Copied directory {item} to {dest}")
                
            return True
            
        except Exception as e:
            logger.error(f"File migration failed: {e}")
            return False
            
    def validate_migration(self) -> bool:
        """Validate the migration by running tests."""
        try:
            # Run pytest for auth-related tests
            result = subprocess.run(
                ['pytest', 'tests/core/test_auth.py', '-v'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Tests failed after migration:\n{result.stdout}\n{result.stderr}")
                return False
                
            logger.info("Migration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
            
    def cleanup(self) -> bool:
        """Clean up old auth directory after successful migration."""
        try:
            shutil.rmtree(self.src_auth)
            logger.info(f"Removed old auth directory at {self.src_auth}")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
            
    def generate_report(self) -> None:
        """Generate migration report."""
        report_path = self.root_dir / 'migration_reports' / f'auth_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(f"# Auth System Migration Report\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Files Updated\n\n")
            for file in sorted(self.updated_files):
                f.write(f"- {file.relative_to(self.root_dir)}\n")
            f.write("\n## Backup Location\n\n")
            f.write(f"Backup created at: {self.backup_dir}\n")
            
        logger.info(f"Migration report generated at {report_path}")
        
    def run(self) -> bool:
        """Run the complete migration process."""
        steps = [
            (self.validate_environment, "Environment validation"),
            (self.create_backup, "Backup creation"),
            (lambda: self.migrate_files(), "File migration"),
            (lambda: self.update_imports(self.find_import_references()), "Import updates"),
            (self.validate_migration, "Migration validation"),
            (self.cleanup, "Cleanup"),
            (self.generate_report, "Report generation")
        ]
        
        for step_func, step_name in steps:
            logger.info(f"Starting: {step_name}")
            if not step_func():
                logger.error(f"Failed at: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")
            
        return True

if __name__ == "__main__":
    migration = AuthMigration()
    if migration.run():
        logger.info("Auth system migration completed successfully")
    else:
        logger.error("Auth system migration failed") 
