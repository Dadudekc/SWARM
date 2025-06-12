"""Tests for the code scanner."""

import pytest
import asyncio
from pathlib import Path
from dreamos.core.verification.scanner import Scanner, ScanResults
from tests.utils.test_environment import TestEnvironment

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for scanner tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def project_dir(test_env: TestEnvironment) -> Path:
    """Get test project directory."""
    project_dir = test_env.get_test_dir("temp") / "scanner_project"
    project_dir.mkdir(exist_ok=True)
    return project_dir

@pytest.fixture
def scanner(project_dir):
    """Create a scanner instance for testing."""
    return Scanner(str(project_dir))

def test_scanner_initialization(test_env: TestEnvironment, project_dir: Path):
    """Test scanner initialization."""
    assert project_dir.exists()
    assert project_dir.is_dir()

def test_detects_duplicate_functions(project_dir, scanner):
    """Test detection of duplicate functions."""
    # Create two files with identical functions
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text("def foo():\n    return 1\n")
    f2.write_text("def foo():\n    return 1\n")

    results = asyncio.run(scanner.scan_project())
    assert results.total_duplicates >= 1
    assert "functions" in results.duplicates

def test_ignores_docstrings_and_comments(project_dir, scanner):
    """Test that docstrings and comments don't affect similarity detection."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text('''def foo():
    """This is a docstring."""
    # This is a comment
    return 1
''')
    f2.write_text('''def foo():
    """Different docstring."""
    # Different comment
    return 1
''')

    results = asyncio.run(scanner.scan_project())
    assert results.total_duplicates >= 1

def test_detects_similar_functions(project_dir, scanner):
    """Test detection of similar but not identical functions."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text('''def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''')
    f2.write_text('''def transform_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''')

    results = asyncio.run(scanner.scan_project())
    assert results.total_duplicates >= 1

def test_handles_nested_functions(project_dir, scanner):
    """Test detection of duplicate nested functions."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text('''def outer():
    def inner():
        return 1
    return inner()
''')
    f2.write_text('''def outer():
    def inner():
        return 1
    return inner()
''')

    results = asyncio.run(scanner.scan_project())
    assert results.total_duplicates >= 2  # Both outer and inner functions

def test_generates_narrative(project_dir, scanner):
    """Test narrative generation in scan results."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text("def foo():\n    return 1\n")
    f2.write_text("def foo():\n    return 1\n")

    results = asyncio.run(scanner.scan_project())
    assert results.narrative
    assert "Code duplication analysis" in results.narrative
    assert "mod1.py" in results.narrative or "mod2.py" in results.narrative

def test_identifies_top_violators(project_dir, scanner):
    """Test identification of files with most duplicates."""
    # Create multiple files with duplicates
    for i in range(3):
        f = project_dir / f"mod{i}.py"
        f.write_text("def foo():\n    return 1\n")

    results = asyncio.run(scanner.scan_project())
    assert results.top_violators
    assert len(results.top_violators) > 0
    assert "count" in results.top_violators[0]

def test_handles_empty_project(project_dir, scanner):
    """Test scanning an empty project."""
    results = asyncio.run(scanner.scan_project())
    assert results.total_files == 0
    assert results.total_duplicates == 0
    assert not results.duplicates

def test_handles_malformed_python(project_dir, scanner):
    """Test handling of malformed Python files."""
    f = project_dir / "bad.py"
    f.write_text("def foo():\n    return 1\n    # Missing closing brace")

    results = asyncio.run(scanner.scan_project())
    assert results.total_files == 0  # Should skip malformed file

def test_respects_similarity_threshold(project_dir):
    """Test that similarity threshold affects detection."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text('''def process(data):
    return [x * 2 for x in data]
''')
    f2.write_text('''def transform(data):
    return [x * 2 for x in data]
''')

    # Test with high threshold
    scanner_high = Scanner(str(project_dir), similarity_threshold=0.95)
    results_high = asyncio.run(scanner_high.scan_project())
    
    # Test with low threshold
    scanner_low = Scanner(str(project_dir), similarity_threshold=0.5)
    results_low = asyncio.run(scanner_low.scan_project())
    
    assert results_high.total_duplicates <= results_low.total_duplicates

def test_output_formats(project_dir, scanner):
    """Test different output formats."""
    f1 = project_dir / "mod1.py"
    f2 = project_dir / "mod2.py"
    f1.write_text("def foo():\n    return 1\n")
    f2.write_text("def foo():\n    return 1\n")

    results = asyncio.run(scanner.scan_project())
    
    # Test JSON format
    json_output = results.summary()
    assert isinstance(json_output, dict)
    assert "type" in json_output
    assert "total_duplicates" in json_output
    
    # Test text format
    text_output = results.format_full_report()
    assert isinstance(text_output, str)
    assert "Scan Summary" in text_output 