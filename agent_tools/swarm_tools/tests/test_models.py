import pytest
from pathlib import Path
import datetime
from agent_tools.scanner.models.analysis import ClassInfo, FileAnalysis, ProjectAnalysis

def test_class_info_initialization():
    """Test ClassInfo initialization."""
    class_info = ClassInfo(
        name="TestClass",
        methods=["method1", "method2"],
        docstring="Test class docstring",
        base_classes=["BaseClass"],
        maturity="stable",
        agent_type="core",
        complexity=2,
        dependencies={"dep1", "dep2"}
    )
    
    assert class_info.name == "TestClass"
    assert len(class_info.methods) == 2
    assert class_info.docstring == "Test class docstring"
    assert len(class_info.base_classes) == 1
    assert class_info.maturity == "stable"
    assert class_info.agent_type == "core"
    assert class_info.complexity == 2
    assert len(class_info.dependencies) == 2

def test_file_analysis_initialization():
    """Test FileAnalysis initialization."""
    file_analysis = FileAnalysis(
        path=Path("test.py"),
        language=".py",
        functions=["func1", "func2"],
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
        routes=["/test"],
        complexity=3,
        dependencies={"dep1"},
        imports={"import1"},
        test_coverage=0.8,
        cyclomatic_complexity=5,
        duplicate_lines=2
    )
    
    assert file_analysis.path == Path("test.py")
    assert file_analysis.language == ".py"
    assert len(file_analysis.functions) == 2
    assert len(file_analysis.classes) == 1
    assert len(file_analysis.routes) == 1
    assert file_analysis.complexity == 3
    assert len(file_analysis.dependencies) == 1
    assert len(file_analysis.imports) == 1
    assert file_analysis.test_coverage == 0.8
    assert file_analysis.cyclomatic_complexity == 5
    assert file_analysis.duplicate_lines == 2

def test_project_analysis_initialization():
    """Test ProjectAnalysis initialization."""
    project_analysis = ProjectAnalysis(
        project_root=Path("."),
        scan_time=datetime.datetime(2024, 1, 1, 0, 0, 0),
        files={
            "test.py": FileAnalysis(
                path=Path("test.py"),
                language=".py",
                functions=[],
                classes={},
                routes=[],
                complexity=1,
                dependencies=set(),
                imports=set(),
                test_coverage=0.0,
                cyclomatic_complexity=1,
                duplicate_lines=0
            )
        },
        dependencies={"dep1": {"dep2"}},
        circular_dependencies=[["file1.py", "file2.py"]],
        modules={"module1": {"file1.py", "file2.py"}},
        core_components={"core1.py"},
        peripheral_components={"peripheral1.py"},
        test_files={"test_file.py": FileAnalysis(
            path=Path("test_file.py"),
            language=".py",
            functions=[],
            classes={},
            routes=[],
            complexity=1,
            dependencies=set(),
            imports=set(),
            test_coverage=0.0,
            cyclomatic_complexity=1,
            duplicate_lines=0
        )},
        total_complexity=10,
        total_duplication=5,
        average_test_coverage=0.75
    )
    
    assert project_analysis.project_root == Path(".")
    assert project_analysis.scan_time == datetime.datetime(2024, 1, 1, 0, 0, 0)
    assert len(project_analysis.files) == 1
    assert len(project_analysis.dependencies) == 1
    assert len(project_analysis.circular_dependencies) == 1
    assert len(project_analysis.modules) == 1
    assert len(project_analysis.core_components) == 1
    assert len(project_analysis.peripheral_components) == 1
    assert len(project_analysis.test_files) == 1
    assert project_analysis.total_complexity == 10
    assert project_analysis.total_duplication == 5
    assert project_analysis.average_test_coverage == 0.75

def test_project_analysis_to_dict():
    """Test ProjectAnalysis to_dict method."""
    project_analysis = ProjectAnalysis(
        project_root=Path("."),
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
    
    result = project_analysis.to_dict()
    assert isinstance(result, dict)
    assert "project_root" in result
    assert "scan_time" in result
    assert "files" in result
    assert "dependencies" in result
    assert "circular_dependencies" in result
    assert "modules" in result
    assert "core_components" in result
    assert "peripheral_components" in result
    assert "test_files" in result
    assert "total_complexity" in result
    assert "total_duplication" in result
    assert "average_test_coverage" in result 