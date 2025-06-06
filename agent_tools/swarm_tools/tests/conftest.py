import pytest
from pathlib import Path
import tempfile
import os
import datetime

from agent_tools.swarm_tools.models.analysis import FileAnalysis, ClassInfo
from agent_tools.swarm_tools.scanner import Scanner

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Create sample Python files
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        
        # Create source files
        with open(project_dir / "src" / "file1.py", "w") as f:
            f.write("""
def func1():
    pass

class TestClass:
    def method1(self):
        pass
""")
        
        with open(project_dir / "src" / "file2.py", "w") as f:
            f.write("""
from .file1 import TestClass

def func2():
    pass
""")
        
        # Create test files
        with open(project_dir / "tests" / "test_file1.py", "w") as f:
            f.write("""
def test_func1():
    pass
""")
        
        yield project_dir

@pytest.fixture
def sample_file_analysis():
    """Create a sample FileAnalysis object."""
    return FileAnalysis(
        path=Path("test.py"),
        language=".py",
        functions=["func1", "func2"],
        classes={
            "TestClass": ClassInfo(
                name="TestClass",
                methods=["method1"],
                docstring="Test class",
                base_classes=["BaseClass"],
                maturity="stable",
                agent_type="core",
                complexity=2,
                dependencies={"dep1"}
            )
        },
        routes=["/test"],
        complexity=3,
        dependencies={"dep1"},
        imports={"import1"},
        test_coverage=0.8,
        cyclomatic_complexity=5,
        duplicate_lines=2
    )

@pytest.fixture
def sample_project_analysis(temp_project_dir):
    """Create a sample ProjectAnalysis object."""
    from agent_tools.scanner.models.analysis import ProjectAnalysis
    
    return ProjectAnalysis(
        project_root=temp_project_dir,
        scan_time=datetime.datetime(2024, 1, 1, 0, 0, 0),
        files={
            "src/file1.py": FileAnalysis(
                path=Path("src/file1.py"),
                language=".py",
                functions=["func1"],
                classes={
                    "TestClass": ClassInfo(
                        name="TestClass",
                        methods=["method1"],
                        docstring="",
                        base_classes=[],
                        maturity="stable",
                        agent_type="core",
                        complexity=1,
                        dependencies=set()
                    )
                },
                routes=[],
                complexity=2,
                dependencies=set(),
                imports=set(),
                test_coverage=0.0,
                cyclomatic_complexity=2,
                duplicate_lines=0
            )
        },
        dependencies={"src/file1.py": {"src/file2.py"}},
        circular_dependencies=[],
        modules={"src": {"src/file1.py", "src/file2.py"}},
        core_components={"src/file1.py"},
        peripheral_components={"src/file2.py"},
        test_files={"tests/test_file1.py"},
        total_complexity=2,
        total_duplication=0,
        average_test_coverage=0.0
    ) 