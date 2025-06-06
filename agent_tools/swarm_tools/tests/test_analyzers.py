import pytest
from pathlib import Path
import tempfile

from agent_tools.scanner.analyzers.dependency_analyzer import DependencyAnalyzer
from agent_tools.scanner.analyzers.quality_analyzer import QualityAnalyzer
from agent_tools.scanner.models.analysis import FileAnalysis

@pytest.fixture
def sample_files():
    """Create sample files for testing."""
    files = {
        "file1.py": FileAnalysis(
            path=Path("file1.py"),
            language=".py",
            functions=["func1"],
            classes={},
            routes=[],
            complexity=1,
            dependencies=set(),
            imports={"file2.py"},
            test_coverage=0.0,
            cyclomatic_complexity=1,
            duplicate_lines=0
        ),
        "file2.py": FileAnalysis(
            path=Path("file2.py"),
            language=".py",
            functions=["func2"],
            classes={},
            routes=[],
            complexity=1,
            dependencies=set(),
            imports={"file3.py"},
            test_coverage=0.0,
            cyclomatic_complexity=1,
            duplicate_lines=0
        ),
        "file3.py": FileAnalysis(
            path=Path("file3.py"),
            language=".py",
            functions=["func3"],
            classes={},
            routes=[],
            complexity=1,
            dependencies=set(),
            imports={"file1.py"},
            test_coverage=0.0,
            cyclomatic_complexity=1,
            duplicate_lines=0
        )
    }
    return files

def test_dependency_analyzer_initialization():
    """Test dependency analyzer initialization."""
    analyzer = DependencyAnalyzer(Path("."))
    assert analyzer.project_root.is_absolute()

def test_analyze_dependencies(sample_files):
    """Test dependency analysis."""
    analyzer = DependencyAnalyzer(Path("."))
    dependencies, circular_deps = analyzer.analyze_dependencies(sample_files)
    
    assert len(dependencies) == 3
    assert len(circular_deps) > 0  # Should detect circular dependency between file1, file2, file3

def test_identify_core_components(sample_files):
    """Test identification of core and peripheral components."""
    analyzer = DependencyAnalyzer(Path("."))
    
    # Set up imports to make file2.py clearly peripheral
    sample_files["file1.py"].imports = {"file3.py"}
    sample_files["file2.py"].imports = {"file3.py"}  # Only depends on one file
    sample_files["file3.py"].imports = {"file1.py"}  # Creates a cycle with file1
    
    # Use absolute paths for assertions
    abs_file1 = str(Path("file1.py").absolute())
    abs_file2 = str(Path("file2.py").absolute())
    abs_file3 = str(Path("file3.py").absolute())
    
    # Analyze dependencies and pass to identify_core_components
    dependencies, _ = analyzer.analyze_dependencies(sample_files)
    core, peripheral = analyzer.identify_core_components(sample_files, dependencies)
    
    # file1.py and file3.py should be core (they form a cycle)
    assert abs_file1 in core
    assert abs_file3 in core
    
    # file2.py should be peripheral (only depends on one file)
    assert abs_file2 in peripheral

def test_group_into_modules(sample_files):
    """Test module grouping."""
    analyzer = DependencyAnalyzer(Path("."))
    modules = analyzer.group_into_modules(sample_files)
    
    assert len(modules) > 0
    assert all(isinstance(files, set) for files in modules.values())

def test_quality_analyzer_initialization():
    """Test quality analyzer initialization."""
    analyzer = QualityAnalyzer()
    assert analyzer.cyclomatic_complexity is not None

def test_analyze_file_quality():
    """Test file quality analysis."""
    analyzer = QualityAnalyzer()
    source_code = """
def test_func():
    if True:
        for i in range(10):
            while i > 0:
                pass
    return True
"""
    complexity, duplication = analyzer.analyze_file_quality(Path("test.py"), source_code)
    
    assert complexity > 0
    assert duplication >= 0

def test_analyze_test_coverage():
    """Test test coverage analysis."""
    analyzer = QualityAnalyzer()
    test_files = {
        "tests/test_file.py": FileAnalysis(
            path=Path("tests/test_file.py"),
            language=".py",
            functions=["test_func"],
            classes={},
            routes=[],
            complexity=2,
            dependencies=set(),
            imports=set(),
            test_coverage=0.0,
            cyclomatic_complexity=2,
            duplicate_lines=0
        )
    }
    source_files = {
        "file.py": FileAnalysis(
            path=Path("file.py"),
            language=".py",
            functions=["func"],
            classes={},
            routes=[],
            complexity=1,
            dependencies=set(),
            imports=set(),
            test_coverage=0.0,
            cyclomatic_complexity=1,
            duplicate_lines=0
        )
    }
    
    coverage = analyzer.analyze_test_coverage(test_files, source_files)
    assert len(coverage) == 1
    assert coverage["file.py"] > 0 