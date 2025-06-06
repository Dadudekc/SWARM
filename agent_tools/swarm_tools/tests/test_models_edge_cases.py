import pytest
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Set

from agent_tools.scanner.models.analysis import ClassInfo, FileAnalysis, ProjectAnalysis

def test_class_info_edge_cases():
    """Test ClassInfo with edge cases."""
    # Test with empty values
    empty_class = ClassInfo(
        name="EmptyClass",
        methods=[],
        docstring="",
        base_classes=[],
        maturity="",
        agent_type="",
        complexity=0,
        dependencies=set()
    )
    assert empty_class.name == "EmptyClass"
    assert len(empty_class.methods) == 0
    assert empty_class.docstring == ""
    assert len(empty_class.base_classes) == 0
    assert empty_class.maturity == ""
    assert empty_class.agent_type == ""
    assert empty_class.complexity == 0
    assert len(empty_class.dependencies) == 0
    
    # Test with maximum values
    max_class = ClassInfo(
        name="MaxClass",
        methods=["method" + str(i) for i in range(1000)],
        docstring="x" * 10000,  # Very long docstring
        base_classes=["Base" + str(i) for i in range(100)],
        maturity="stable",
        agent_type="core",
        complexity=1000,
        dependencies={"dep" + str(i) for i in range(100)}
    )
    assert len(max_class.methods) == 1000
    assert len(max_class.docstring) == 10000
    assert len(max_class.base_classes) == 100
    assert len(max_class.dependencies) == 100

def test_file_analysis_edge_cases():
    """Test FileAnalysis with edge cases."""
    # Test with empty values
    empty_file = FileAnalysis(
        path=Path("empty.py"),
        language=".py",
        functions=[],
        classes={},
        routes=[],
        complexity=0,
        dependencies=set(),
        imports=set(),
        test_coverage=0.0,
        cyclomatic_complexity=0,
        duplicate_lines=0
    )
    assert empty_file.path == Path("empty.py")
    assert len(empty_file.functions) == 0
    assert len(empty_file.classes) == 0
    assert len(empty_file.routes) == 0
    assert empty_file.complexity == 0
    assert len(empty_file.dependencies) == 0
    assert len(empty_file.imports) == 0
    assert empty_file.test_coverage == 0.0
    assert empty_file.cyclomatic_complexity == 0
    assert empty_file.duplicate_lines == 0
    
    # Test with maximum values
    max_file = FileAnalysis(
        path=Path("max.py"),
        language=".py",
        functions=["func" + str(i) for i in range(1000)],
        classes={
            f"Class{i}": ClassInfo(
                name=f"Class{i}",
                methods=["method" + str(j) for j in range(100)],
                docstring="",
                base_classes=[],
                maturity="stable",
                agent_type="core",
                complexity=100,
                dependencies=set()
            )
            for i in range(100)
        },
        routes=["/route" + str(i) for i in range(100)],
        complexity=1000,
        dependencies={"dep" + str(i) for i in range(100)},
        imports={"imp" + str(i) for i in range(100)},
        test_coverage=1.0,
        cyclomatic_complexity=1000,
        duplicate_lines=1000
    )
    assert len(max_file.functions) == 1000
    assert len(max_file.classes) == 100
    assert len(max_file.routes) == 100
    assert max_file.complexity == 1000
    assert len(max_file.dependencies) == 100
    assert len(max_file.imports) == 100
    assert max_file.test_coverage == 1.0
    assert max_file.cyclomatic_complexity == 1000
    assert max_file.duplicate_lines == 1000

def test_project_analysis_edge_cases():
    """Test ProjectAnalysis with edge cases."""
    # Test with empty values
    empty_project = ProjectAnalysis(
        project_root=Path("."),
        scan_time=datetime.now(),
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
    assert empty_project.project_root == Path(".")
    assert len(empty_project.files) == 0
    assert len(empty_project.dependencies) == 0
    assert len(empty_project.circular_dependencies) == 0
    assert len(empty_project.modules) == 0
    assert len(empty_project.core_components) == 0
    assert len(empty_project.peripheral_components) == 0
    assert len(empty_project.test_files) == 0
    assert empty_project.total_complexity == 0
    assert empty_project.total_duplication == 0
    assert empty_project.average_test_coverage == 0.0
    
    # Test with maximum values
    max_project = ProjectAnalysis(
        project_root=Path("."),
        scan_time=datetime.now(),
        files={
            f"file{i}.py": FileAnalysis(
                path=Path(f"file{i}.py"),
                language=".py",
                functions=["func" + str(j) for j in range(100)],
                classes={},
                routes=[],
                complexity=100,
                dependencies=set(),
                imports=set(),
                test_coverage=1.0,
                cyclomatic_complexity=100,
                duplicate_lines=100
            )
            for i in range(1000)
        },
        dependencies={
            f"file{i}.py": {f"file{j}.py" for j in range(100)}
            for i in range(1000)
        },
        circular_dependencies=[
            [f"file{i}.py" for i in range(10)]
            for _ in range(100)
        ],
        modules={
            f"module{i}": {f"file{j}.py" for j in range(100)}
            for i in range(10)
        },
        core_components={f"file{i}.py" for i in range(500)},
        peripheral_components={f"file{i}.py" for i in range(500, 1000)},
        test_files={
            f"test_file{i}.py": FileAnalysis(
                path=Path(f"test_file{i}.py"),
                language=".py",
                functions=["test_func" + str(j) for j in range(100)],
                classes={},
                routes=[],
                complexity=100,
                dependencies=set(),
                imports=set(),
                test_coverage=1.0,
                cyclomatic_complexity=100,
                duplicate_lines=100
            )
            for i in range(1000)
        },
        total_complexity=100000,
        total_duplication=100000,
        average_test_coverage=1.0
    )
    assert len(max_project.files) == 1000
    assert len(max_project.dependencies) == 1000
    assert len(max_project.circular_dependencies) == 100
    assert len(max_project.modules) == 10
    assert len(max_project.core_components) == 500
    assert len(max_project.peripheral_components) == 500
    assert len(max_project.test_files) == 1000
    assert max_project.total_complexity == 100000
    assert max_project.total_duplication == 100000
    assert max_project.average_test_coverage == 1.0

def test_serialization_edge_cases():
    """Test serialization of models with edge cases."""
    # Test ClassInfo serialization
    class_info = ClassInfo(
        name="TestClass",
        methods=["method1", "method2"],
        docstring="Test docstring",
        base_classes=["Base1", "Base2"],
        maturity="stable",
        agent_type="core",
        complexity=10,
        dependencies={"dep1", "dep2"}
    )
    class_dict = class_info.to_dict()
    assert isinstance(class_dict, dict)
    assert class_dict["name"] == "TestClass"
    assert len(class_dict["methods"]) == 2
    assert class_dict["docstring"] == "Test docstring"
    assert len(class_dict["base_classes"]) == 2
    assert class_dict["maturity"] == "stable"
    assert class_dict["agent_type"] == "core"
    assert class_dict["complexity"] == 10
    assert len(class_dict["dependencies"]) == 2
    
    # Test FileAnalysis serialization
    file_analysis = FileAnalysis(
        path=Path("test.py"),
        language=".py",
        functions=["func1", "func2"],
        classes={
            "TestClass": class_info
        },
        routes=["/test"],
        complexity=20,
        dependencies={"dep1"},
        imports={"imp1"},
        test_coverage=0.8,
        cyclomatic_complexity=20,
        duplicate_lines=5
    )
    file_dict = file_analysis.to_dict()
    assert isinstance(file_dict, dict)
    assert file_dict["path"] == str(Path("test.py"))
    assert len(file_dict["functions"]) == 2
    assert len(file_dict["classes"]) == 1
    assert len(file_dict["routes"]) == 1
    assert file_dict["complexity"] == 20
    assert len(file_dict["dependencies"]) == 1
    assert len(file_dict["imports"]) == 1
    assert file_dict["test_coverage"] == 0.8
    assert file_dict["cyclomatic_complexity"] == 20
    assert file_dict["duplicate_lines"] == 5
    
    # Test ProjectAnalysis serialization
    project_analysis = ProjectAnalysis(
        project_root=Path("."),
        scan_time=datetime.now(),
        files={"test.py": file_analysis},
        dependencies={"test.py": {"dep1"}},
        circular_dependencies=[["file1.py", "file2.py"]],
        modules={"module1": {"file1.py", "file2.py"}},
        core_components={"core1.py"},
        peripheral_components={"peripheral1.py"},
        test_files={"test_file.py": file_analysis},
        total_complexity=20,
        total_duplication=5,
        average_test_coverage=0.8
    )
    project_dict = project_analysis.to_dict()
    assert isinstance(project_dict, dict)
    assert project_dict["project_root"] == str(Path("."))
    assert len(project_dict["files"]) == 1
    assert len(project_dict["dependencies"]) == 1
    assert len(project_dict["circular_dependencies"]) == 1
    assert len(project_dict["modules"]) == 1
    assert len(project_dict["core_components"]) == 1
    assert len(project_dict["peripheral_components"]) == 1
    assert len(project_dict["test_files"]) == 1
    assert project_dict["total_complexity"] == 20
    assert project_dict["total_duplication"] == 5
    assert project_dict["average_test_coverage"] == 0.8 