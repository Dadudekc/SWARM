import pytest
import asyncio
from pathlib import Path
import tempfile
import os
import json
from datetime import datetime

from agent_tools.swarm_tools.scanner import Scanner
from agent_tools.swarm_tools.core.scan_results import ScanResults

@pytest.fixture
def complex_project():
    """Create a complex project structure with various edge cases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Create nested directory structure
        (project_dir / "src" / "core" / "utils").mkdir(parents=True)
        (project_dir / "src" / "api" / "v1").mkdir(parents=True)
        (project_dir / "tests" / "unit" / "core").mkdir(parents=True)
        
        # Create files with circular dependencies
        with open(project_dir / "src" / "core" / "file1.py", "w") as f:
            f.write("""
from ..api.v1.file2 import ClassB

class ClassA:
    def method_a(self):
        return ClassB().method_b()
""")
            
        with open(project_dir / "src" / "api" / "v1" / "file2.py", "w") as f:
            f.write("""
from ...core.file1 import ClassA

class ClassB:
    def method_b(self):
        return ClassA().method_a()
""")
            
        # Create file with complex code structure
        with open(project_dir / "src" / "core" / "utils" / "complex.py", "w") as f:
            f.write("""
def complex_function():
    try:
        for i in range(10):
            while i > 0:
                if i % 2 == 0:
                    try:
                        pass
                    except Exception:
                        pass
                else:
                    pass
    except Exception:
        pass
    finally:
        pass
""")
            
        # Create test files
        with open(project_dir / "tests" / "unit" / "core" / "test_file1.py", "w") as f:
            f.write("""
def test_class_a():
    pass

def test_method_a():
    pass
""")
            
        yield project_dir

@pytest.mark.asyncio
async def test_complex_project_scan(complex_project):
    """Test scanning a complex project with circular dependencies."""
    scanner = Scanner(complex_project)
    results = await scanner.scan()
    
    assert isinstance(results, ScanResults)
    assert results.total_files > 0
    
    # Check for circular dependencies in architectural issues
    circular_deps = [issue for issue in results.architectural_issues 
                    if "circular dependency" in issue.get('description', '').lower()]
    assert len(circular_deps) > 0
    
    # Verify the files were analyzed
    file_paths = [str(Path(complex_project) / "src" / "core" / "file1.py"),
                 str(Path(complex_project) / "src" / "api" / "v1" / "file2.py")]
    for path in file_paths:
        assert any(path in issue.get('location', '') for issue in results.architectural_issues)

@pytest.mark.asyncio
async def test_complex_code_analysis(complex_project):
    """Test analysis of complex code structures."""
    scanner = Scanner(complex_project)
    results = await scanner.scan()
    
    # Find the complex.py file analysis
    complex_file = Path(complex_project) / "src" / "core" / "utils" / "complex.py"
    complex_analysis = None
    
    for issue in results.architectural_issues:
        if str(complex_file) in issue.get('location', ''):
            complex_analysis = issue
            break
    
    assert complex_analysis is not None
    assert "complex" in complex_analysis.get('description', '').lower()
    assert "complex_function" in complex_analysis.get('location', '')

@pytest.mark.asyncio
async def test_empty_project():
    """Test scanning an empty project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        scanner = Scanner(temp_dir)
        results = await scanner.scan()
        
        assert isinstance(results, ScanResults)
        assert results.total_files == 0
        assert results.total_duplicates == 0
        assert len(results.duplicates) == 0
        assert len(results.architectural_issues) == 0
        assert len(results.agent_categories) == 0
        assert len(results.structural_insights) == 0
        assert len(results.themes) == 0
        assert results.scan_time >= 0

@pytest.mark.asyncio
async def test_invalid_files(complex_project):
    """Test handling of invalid Python files."""
    # Create an invalid Python file
    invalid_file = Path(complex_project) / "src" / "invalid.py"
    invalid_file.write_text("""
def invalid_function()
    pass  # Missing colon
""")
    
    scanner = Scanner(complex_project)
    results = await scanner.scan()
    
    # Check for syntax error in architectural issues
    syntax_errors = [issue for issue in results.architectural_issues 
                    if "syntax error" in issue.get('description', '').lower()]
    assert len(syntax_errors) > 0
    assert any(str(invalid_file) in issue.get('location', '') for issue in syntax_errors)

@pytest.mark.asyncio
async def test_large_file_handling(complex_project):
    """Test handling of large files."""
    # Create a large file
    large_file = Path(complex_project) / "src" / "large.py"
    with large_file.open("w") as f:
        for i in range(1000):
            f.write(f"def function_{i}():\n    pass\n\n")
    
    scanner = Scanner(complex_project)
    results = await scanner.scan()
    
    # Check for large file analysis
    large_file_issues = [issue for issue in results.architectural_issues 
                        if str(large_file) in issue.get('location', '')]
    assert len(large_file_issues) > 0
    
    # Verify functions were detected
    function_count = sum(1 for issue in large_file_issues 
                        if "function" in issue.get('description', '').lower())
    assert function_count > 0

@pytest.mark.asyncio
async def test_ignore_patterns_complex(complex_project):
    """Test complex ignore patterns."""
    scanner = Scanner(complex_project)
    
    # Ignore all core files
    scanner.file_manager.ignore_patterns = ["**/core/**"]
    results = await scanner.scan()
    
    # Verify core files were ignored
    core_files = [issue for issue in results.architectural_issues 
                 if "/core/" in issue.get('location', '')]
    assert len(core_files) == 0
    
    # Ignore specific file types
    scanner.file_manager.ignore_patterns = ["**/*.pyc", "**/__pycache__/**"]
    results = await scanner.scan()
    
    # Verify all Python files were still processed
    python_files = [issue for issue in results.architectural_issues 
                   if issue.get('location', '').endswith('.py')]
    assert len(python_files) > 0

@pytest.mark.asyncio
async def test_concurrent_file_processing(complex_project):
    """Test concurrent processing of multiple files."""
    scanner = Scanner(complex_project)
    
    # Create multiple files simultaneously
    for i in range(10):
        file_path = Path(complex_project) / "src" / f"concurrent_{i}.py"
        file_path.write_text(f"def function_{i}():\n    pass\n")
    
    results = await scanner.scan()
    
    # Verify all files were processed
    concurrent_files = [issue for issue in results.architectural_issues 
                      if "concurrent_" in issue.get('location', '')]
    assert len(concurrent_files) >= 10

@pytest.mark.asyncio
async def test_save_results_complex(complex_project):
    """Test saving results for a complex project."""
    scanner = Scanner(complex_project)
    results = await scanner.scan()
    
    # Save results
    assert scanner.save_results(results)
    
    # Verify all result files were created
    reports_dir = Path(complex_project) / "reports"
    assert reports_dir.exists()
    assert (reports_dir / "scan_results.json").exists()
    assert (reports_dir / "scan_results.html").exists()
    assert (reports_dir / "scan_results.txt").exists()
    
    # Verify JSON content
    with open(reports_dir / "scan_results.json") as f:
        data = json.load(f)
        assert "total_files" in data
        assert "total_duplicates" in data
        assert "architectural_issues" in data
        assert "themes" in data 
