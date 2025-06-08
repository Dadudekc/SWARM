#!/usr/bin/env python3
"""
Generate missing test stubs for untested modules.
"""

import os
import ast
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Constants
SOURCE_DIR = "dreamos"
TEST_DIR = "tests"
KEEPLIST_FILE = "tests/test_keeplist.yaml"

def get_module_type(module_path: Path) -> str:
    """Determine if module is a package or module."""
    if module_path.is_dir() and (module_path / "__init__.py").exists():
        return "package"
    return "module"

def get_functions(module_path: Path) -> List[str]:
    """Extract function names from a Python module."""
    if not module_path.is_file():
        return []
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    except Exception as e:
        print(f"Error parsing {module_path}: {e}")
        return []

def generate_test_stub(module_path: Path, functions: List[str]) -> str:
    """Generate test stub content for a module."""
    # Convert path to proper Python import path
    rel_path = module_path.relative_to(SOURCE_DIR)
    import_path = f"dreamos.{str(rel_path).replace(os.sep, '.').replace('.py', '')}"
    module_name = rel_path.stem
    
    # Generate imports
    imports = [
        "import pytest",
        f"from {import_path} import {', '.join(functions)}",
        "",
        "# Fixtures",
        "@pytest.fixture",
        "def sample_data():",
        "    return {}",
        ""
    ]
    
    # Generate test functions
    test_functions = []
    for func in functions:
        test_functions.extend([
            f"@pytest.mark.skip(reason='Pending implementation')",
            f"def test_{func}(sample_data):",
            f"    \"\"\"Test {func} function.\"\"\"",
            f"    # TODO: Implement test",
            f"    pass",
            ""
        ])
    
    # Combine all parts
    content = [
        f"\"\"\"Tests for {module_name} module.\"\"\"",
        "",
        *imports,
        *test_functions
    ]
    
    return "\n".join(content)

def ensure_test_dir(test_path: Path) -> None:
    """Ensure test directory exists."""
    test_path.parent.mkdir(parents=True, exist_ok=True)

def main():
    # Load keeplist
    with open(KEEPLIST_FILE, 'r', encoding='utf-8') as f:
        keeplist = yaml.safe_load(f)
    
    # Find all Python modules
    source_path = Path(SOURCE_DIR)
    test_path = Path(TEST_DIR)
    
    for root, _, files in os.walk(source_path):
        for file in files:
            if not file.endswith('.py') or file.startswith('__'):
                continue
                
            module_path = Path(root) / file
            rel_path = module_path.relative_to(source_path)
            test_file = test_path / rel_path.with_name(f"test_{rel_path.stem}.py")
            
            # Skip if in keeplist
            if str(test_file.relative_to(test_path)) in keeplist:
                continue
            
            # Generate test stub
            functions = get_functions(module_path)
            if functions:
                content = generate_test_stub(module_path, functions)
                ensure_test_dir(test_file)
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Generated: {test_file}")

if __name__ == "__main__":
    main() 