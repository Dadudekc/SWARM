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
from agent_tools.swarm_tools.models.scan_results import ScanResults

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
    assert scanner.file_manager is not None
    assert scanner.report_manager is not None
    assert scanner.analyzer is not None
    assert scanner.architecture_analyzer is not None
    assert scanner.agent_analyzer is not None
    assert scanner.structure_analyzer is not None
    assert scanner.theme_analyzer is not None
    assert scanner.reporter_factory is not None

@pytest.mark.asyncio
async def test_scan_project(temp_project):
    """Test project scanning."""
    scanner = Scanner(temp_project)
    results = await scanner.scan()
    
    assert isinstance(results, ScanResults)
    assert results.total_files > 0
    assert results.total_duplicates >= 0
    assert isinstance(results.duplicates, list)
    assert isinstance(results.architectural_issues, list)
    assert isinstance(results.agent_categories, list)
    assert isinstance(results.structural_insights, list)
    assert isinstance(results.themes, list)
    assert isinstance(results.narrative, str)
    assert isinstance(results.scan_time, float)
    
    # Check if reports were created
    reports_dir = Path(temp_project) / "reports"
    assert reports_dir.exists()
    assert (reports_dir / "scan_results.json").exists()
    assert (reports_dir / "scan_results.html").exists()
    assert (reports_dir / "scan_results.txt").exists()

@pytest.mark.asyncio
async def test_file_processing(temp_project):
    """Test individual file processing."""
    scanner = Scanner(temp_project)
    file_path = Path(temp_project) / "test_file.py"
    
    # Analyze the file
    node_dicts = scanner.analyzer.analyze_file(file_path)
    assert node_dicts is not None
    assert len(node_dicts) > 0
    
    # Check for expected functions and classes
    found_functions = [d['name'] for d in node_dicts if d.get('type') == 'function']
    found_classes = [d['name'] for d in node_dicts if d.get('type') == 'class']
    
    assert "test_function" in found_functions
    assert "TestClass" in found_classes
    
    # Check for AST nodes
    ast_nodes = [d['ast_node'] for d in node_dicts if 'ast_node' in d]
    assert len(ast_nodes) > 0

@pytest.mark.asyncio
async def test_ignore_patterns(temp_project):
    """Test ignore patterns functionality."""
    scanner = Scanner(temp_project)
    
    # Create a file in the tests directory
    test_file = Path(temp_project) / "tests" / "test_ignore.py"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("""
def test_function():
    pass
""")
    
    # Scan without ignore patterns
    results = await scanner.scan()
    all_files = set(str(p) for p in scanner.file_manager.find_python_files())
    assert str(test_file) in all_files
    
    # Scan with ignore patterns
    scanner.file_manager.ignore_patterns = ["tests/*"]
    results = await scanner.scan()
    filtered_files = set(str(p) for p in scanner.file_manager.find_python_files())
    assert str(test_file) not in filtered_files

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

@pytest.mark.asyncio
async def test_scanner_report_generation():
    """Test scanner report generation."""
    scanner = Scanner(project_root=Path("test_project"))
    
    # Create a ScanResults object with required fields
    results = ScanResults()
    results.scan_time = 0.1
    results.total_files = 1
    results.total_duplicates = 0
    results.duplicates = []
    results.architectural_issues = []
    results.agent_categories = []
    results.structural_insights = []
    results.themes = []
    results.narrative = "Test narrative."
    results.init_files = []
    results.top_violators = []
    results.chatgpt_context = {}
    results.feedback_metrics = {}
    results.bridge_health = {}
    results.discord_integration = {}
    results.ui_metrics = {}
    results.codex_metrics = {}
    
    assert scanner.save_results(results) 
