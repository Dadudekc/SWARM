import pytest
import asyncio
from pathlib import Path
import json
import tempfile
import shutil
import datetime
import os

from agent_tools.swarm_tools.scanner import Scanner
from agent_tools.swarm_tools.models.analysis import FileAnalysis, ProjectAnalysis, ClassInfo

@pytest.fixture
def temp_project():
    """Create a temporary project directory with some test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python file
        python_file = Path(temp_dir) / "test_file.py"
        python_file.write_text("""
def test_function():
    pass

class TestClass:
    def test_method(self):
        pass
""")
        
        # Create a test file
        test_file = Path(temp_dir) / "tests" / "test_test_file.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("""
def test_test_function():
    pass

class TestTestClass:
    def test_test_method(self):
        pass
""")
        
        yield temp_dir

@pytest.mark.asyncio
async def test_scanner_initialization():
    """Test scanner initialization."""
    scanner = Scanner(".")
    assert scanner.project_root.is_absolute()
    assert scanner.dependency_analyzer is not None
    assert scanner.quality_analyzer is not None

@pytest.mark.asyncio
async def test_scan_project(temp_project):
    """Test project scanning."""
    scanner = Scanner(temp_project)
    analysis = await scanner.scan_project()
    
    assert isinstance(analysis, ProjectAnalysis)
    assert analysis.project_root == Path(temp_project)
    assert len(analysis.files) > 0
    assert len(analysis.test_files) > 0
    
    # Check if analysis files were created
    assert (Path(temp_project) / "project_analysis.json").exists()
    assert (Path(temp_project) / "test_analysis.json").exists()
    assert (Path(temp_project) / "chatgpt_project_context.json").exists()

@pytest.mark.asyncio
async def test_file_processing(temp_project):
    """Test individual file processing."""
    scanner = Scanner(temp_project)
    file_path = Path(temp_project) / "test_file.py"
    
    result = await scanner._process_file(file_path)
    assert result is not None
    
    file_path, analysis = result
    assert isinstance(analysis, FileAnalysis)
    assert "test_function" in analysis.functions
    assert "TestClass" in analysis.classes
    assert analysis.language == ".py"

@pytest.mark.asyncio
async def test_ignore_patterns(temp_project):
    """Test ignore patterns functionality."""
    scanner = Scanner(temp_project)
    analysis = await scanner.scan_project(ignore_patterns=["tests"])
    
    assert len(analysis.test_files) == 0
    assert len(analysis.files) > 0

def test_save_results(temp_project):
    """Test saving analysis results."""
    scanner = Scanner(temp_project)
    
    # Create a sample analysis
    analysis = ProjectAnalysis(
        project_root=Path(temp_project),
        scan_time=datetime.datetime(2024, 1, 1, 0, 0, 0),
        files={},
        dependencies={},
        circular_dependencies=[],
        modules={},
        core_components=set(),
        peripheral_components=set(),
        test_files={},
        total_complexity=0,
        total_duplication=0,
        average_test_coverage=0.0
    )
    
    scanner._save_results(analysis)
    
    # Check if files were created
    assert (Path(temp_project) / "project_analysis.json").exists()
    assert (Path(temp_project) / "test_analysis.json").exists()
    assert (Path(temp_project) / "chatgpt_project_context.json").exists()
    
    # Check content
    with open(Path(temp_project) / "project_analysis.json") as f:
        data = json.load(f)
        assert data["project_root"] == str(Path(temp_project)) 
