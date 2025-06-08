import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ProjectCleaner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.archive_dir = self.root_dir / "archive"
        self.report_dir = self.root_dir / "docs" / "project_analysis"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Core directories that should be kept
        self.core_dirs = {
            "dreamos": "Main project code",
            "tests": "Test files",
            "docs": "Documentation",
            "scripts": "Utility scripts",
            "config": "Configuration files",
        }
        
        # Test-related directories to consolidate
        self.test_dirs = {
            "test_logs": "Test logs",
            "test_artifacts": "Test artifacts",
            "test_temp": "Temporary test files",
            "test_data": "Test data",
            ".pytest_cache": "Pytest cache",
        }
        
        # Log files to consolidate
        self.log_patterns = [
            "*.log",
            "*_log.txt",
            "test_*.log",
            "*.log.*",
        ]
        
        # Temporary files to clean
        self.temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.bak",
            "*.swp",
            "*.pyc",
            "__pycache__",
        ]

    def analyze_project(self) -> Dict:
        """Analyze the project structure and generate a report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "total_dirs": 0,
            "file_types": {},
            "test_files": [],
            "log_files": [],
            "temp_files": [],
            "large_files": [],
            "core_dirs": {},
            "test_dirs": {},
        }
        
        # Analyze core directories
        for dir_name, description in self.core_dirs.items():
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                report["core_dirs"][dir_name] = {
                    "description": description,
                    "file_count": len(list(dir_path.rglob("*"))),
                    "size_mb": sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file()) / (1024 * 1024)
                }
        
        # Analyze test directories
        for dir_name, description in self.test_dirs.items():
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                report["test_dirs"][dir_name] = {
                    "description": description,
                    "file_count": len(list(dir_path.rglob("*"))),
                    "size_mb": sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file()) / (1024 * 1024)
                }
        
        # Analyze all files
        for file_path in self.root_dir.rglob("*"):
            if file_path.is_file():
                report["total_files"] += 1
                
                # Skip files in .git directory
                if ".git" in file_path.parts:
                    continue
                
                # Count file types
                ext = file_path.suffix.lower()
                report["file_types"][ext] = report["file_types"].get(ext, 0) + 1
                
                # Check for test files
                if "test" in file_path.name.lower():
                    report["test_files"].append(str(file_path.relative_to(self.root_dir)))
                
                # Check for log files
                if any(file_path.match(pattern) for pattern in self.log_patterns):
                    report["log_files"].append(str(file_path.relative_to(self.root_dir)))
                
                # Check for temp files
                if any(file_path.match(pattern) for pattern in self.temp_patterns):
                    report["temp_files"].append(str(file_path.relative_to(self.root_dir)))
                
                # Check for large files (>1MB)
                if file_path.stat().st_size > 1024 * 1024:
                    report["large_files"].append({
                        "path": str(file_path.relative_to(self.root_dir)),
                        "size_mb": file_path.stat().st_size / (1024 * 1024)
                    })
        
        # Count total directories
        report["total_dirs"] = len([d for d in self.root_dir.rglob("*") if d.is_dir()])
        
        return report

    def generate_report(self, report: Dict) -> None:
        """Generate a detailed report of the analysis."""
        report_path = self.report_dir / f"project_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown summary
        md_path = self.report_dir / f"project_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_path, 'w') as f:
            f.write("# Project Analysis Report\n\n")
            f.write(f"Generated: {report['timestamp']}\n\n")
            
            f.write("## Project Overview\n")
            f.write(f"- Total Files: {report['total_files']}\n")
            f.write(f"- Total Directories: {report['total_dirs']}\n\n")
            
            f.write("## File Types\n")
            for ext, count in sorted(report['file_types'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {ext}: {count} files\n")
            f.write("\n")
            
            f.write("## Core Directories\n")
            for dir_name, info in report['core_dirs'].items():
                f.write(f"### {dir_name}\n")
                f.write(f"- Description: {info['description']}\n")
                f.write(f"- Files: {info['file_count']}\n")
                f.write(f"- Size: {info['size_mb']:.2f} MB\n\n")
            
            f.write("## Test Directories\n")
            for dir_name, info in report['test_dirs'].items():
                f.write(f"### {dir_name}\n")
                f.write(f"- Description: {info['description']}\n")
                f.write(f"- Files: {info['file_count']}\n")
                f.write(f"- Size: {info['size_mb']:.2f} MB\n\n")
            
            if report['test_files']:
                f.write("## Test Files\n")
                for file_path in sorted(report['test_files']):
                    f.write(f"- {file_path}\n")
                f.write("\n")
            
            if report['log_files']:
                f.write("## Log Files\n")
                for file_path in sorted(report['log_files']):
                    f.write(f"- {file_path}\n")
                f.write("\n")
            
            if report['temp_files']:
                f.write("## Temporary Files\n")
                for file_path in sorted(report['temp_files']):
                    f.write(f"- {file_path}\n")
                f.write("\n")
            
            if report['large_files']:
                f.write("## Large Files (>1MB)\n")
                for file_info in sorted(report['large_files'], key=lambda x: x['size_mb'], reverse=True):
                    f.write(f"- {file_info['path']}: {file_info['size_mb']:.2f} MB\n")
                f.write("\n")

    def consolidate_test_files(self) -> None:
        """Consolidate test-related files into a single directory."""
        test_dir = self.root_dir / "tests"
        test_logs_dir = test_dir / "logs"
        test_artifacts_dir = test_dir / "artifacts"
        
        # Create consolidated directories
        test_logs_dir.mkdir(parents=True, exist_ok=True)
        test_artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Move test-related files
        for dir_name in self.test_dirs:
            source_dir = self.root_dir / dir_name
            if source_dir.exists():
                if "log" in dir_name.lower():
                    target_dir = test_logs_dir
                else:
                    target_dir = test_artifacts_dir
                
                # Move files with timestamp to avoid conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(source_dir)
                        target_path = target_dir / f"{relative_path.stem}_{timestamp}{relative_path.suffix}"
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(target_path))
                
                # Remove empty source directory
                if not any(source_dir.iterdir()):
                    source_dir.rmdir()

    def clean_temp_files(self) -> None:
        """Clean temporary files and caches."""
        for pattern in self.temp_patterns:
            for file_path in self.root_dir.rglob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Error removing {file_path}: {e}")
                elif file_path.is_dir():
                    try:
                        shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"Error removing directory {file_path}: {e}")

def main():
    cleaner = ProjectCleaner(".")
    report = cleaner.analyze_project()
    cleaner.generate_report(report)
    
    print("\nProject analysis complete. Report generated in docs/project_analysis/")
    
    # Ask for confirmation before cleanup
    print("\nWould you like to:")
    print("1. Consolidate test files")
    print("2. Clean temporary files")
    print("3. Both")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice in ['1', '3']:
        print("\nConsolidating test files...")
        cleaner.consolidate_test_files()
        print("Test files consolidated!")
    
    if choice in ['2', '3']:
        print("\nCleaning temporary files...")
        cleaner.clean_temp_files()
        print("Temporary files cleaned!")

if __name__ == "__main__":
    main() 
