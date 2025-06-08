import pytest
from pathlib import Path
import tempfile
import os
import shutil
import sys

from agent_tools.scanner.utils.file_utils import (
    is_valid_file,
    is_test_file,
    get_file_extension,
    normalize_path,
    create_directory
)

def test_is_valid_file():
    """Test file validation."""
    # Test Python file
    assert is_valid_file(Path("test.py"), {".py"})
    # Test non-Python file
    assert not is_valid_file(Path("test.txt"), {".py"})
    # Test file with ignored pattern
    assert not is_valid_file(Path("__pycache__/test.py"), {".py"})
    # Test file with multiple extensions
    assert not is_valid_file(Path("test.py.txt"), {".py"})
    # Test file with uppercase extension
    assert is_valid_file(Path("test.PY"), {".py"})
    # Test file with no extension
    assert not is_valid_file(Path("test"), {".py"})
    # Test file with invalid characters
    assert not is_valid_file(Path("test*.py"), {".py"})
    assert not is_valid_file(Path("test?.py"), {".py"})
    assert not is_valid_file(Path("test:.py"), {".py"})

def test_is_test_file():
    """Test test file detection."""
    # Test test file in tests directory
    assert is_test_file(Path("tests/test_file.py"))
    # Test non-test file in root
    assert not is_test_file(Path("file.py"))
    # Test test file in root (should NOT be classified as test file)
    assert not is_test_file(Path("test_file.py"))
    # Test test file in subdirectory
    assert is_test_file(Path("src/tests/test_file.py"))
    # Test non-test file in subdirectory
    assert not is_test_file(Path("src/file.py"))
    # Test test file with different patterns
    assert is_test_file(Path("test_file_test.py"))
    assert is_test_file(Path("test_file_spec.py"))
    assert is_test_file(Path("test_file_suite.py"))
    # Test test file with different extensions
    assert is_test_file(Path("test_file.pyc"))
    assert is_test_file(Path("test_file.pyo"))
    # Test test file with different cases
    assert is_test_file(Path("TestFile.py"))
    assert is_test_file(Path("TEST_FILE.py"))

def test_get_file_extension():
    """Test file extension extraction."""
    assert get_file_extension(Path("test.py")) == ".py"
    assert get_file_extension(Path("test.txt")) == ".txt"
    assert get_file_extension(Path("test")) == ""
    # Test multiple extensions
    assert get_file_extension(Path("test.py.txt")) == ".txt"
    # Test uppercase extension
    assert get_file_extension(Path("test.PY")) == ".PY"
    # Test hidden files
    assert get_file_extension(Path(".test.py")) == ".py"
    # Test files with dots in name
    assert get_file_extension(Path("test.file.py")) == ".py"
    # Test files with no extension
    assert get_file_extension(Path("testfile")) == ""
    # Test files with invalid characters
    assert get_file_extension(Path("test*.py")) == ".py"
    assert get_file_extension(Path("test?.py")) == ".py"

def test_normalize_path():
    """Test path normalization."""
    # Test relative path
    assert normalize_path(Path("test.py")) == Path("test.py")
    # Test absolute path
    abs_path = Path("/absolute/path/test.py")
    assert normalize_path(abs_path) == abs_path
    # Test path with parent directory
    assert normalize_path(Path("../test.py")) == Path("../test.py")
    # Test path with current directory
    assert normalize_path(Path("./test.py")) == Path("test.py")
    # Test path with multiple parent directories
    assert normalize_path(Path("../../test.py")) == Path("../../test.py")
    # Test path with multiple separators
    assert normalize_path(Path("test//file.py")) == Path("test/file.py")
    # Test path with trailing separator
    assert normalize_path(Path("test/")) == Path("test")
    # Test path with invalid characters
    with pytest.raises(ValueError):
        normalize_path(Path("test*.py"))
    with pytest.raises(ValueError):
        normalize_path(Path("test?.py"))
    with pytest.raises(ValueError):
        normalize_path(Path("test:.py"))

def test_create_directory():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        create_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_create_directory_existing():
    """Test directory creation when directory already exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        # Create directory first
        os.makedirs(test_dir)
        # Try to create it again
        create_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_create_directory_with_parents():
    """Test directory creation with parent directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "parent" / "child" / "test_dir"
        create_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert test_dir.parent.exists()
        assert test_dir.parent.parent.exists()

def test_create_directory_permission_error():
    """Test directory creation with permission error."""
    if sys.platform.startswith("win"):
        pytest.skip("Permission errors for directory creation are not reliably testable on Windows.")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory we can't write to
        test_dir = Path(temp_dir) / "test_dir"
        os.makedirs(test_dir)
        os.chmod(test_dir, 0o444)  # Read-only
        
        # Try to create a subdirectory
        sub_dir = test_dir / "sub_dir"
        with pytest.raises(PermissionError):
            create_directory(sub_dir)

def test_create_directory_invalid_path():
    """Test directory creation with invalid path."""
    with pytest.raises(ValueError):
        create_directory(Path("test*.dir"))
    with pytest.raises(ValueError):
        create_directory(Path("test?.dir"))
    with pytest.raises(ValueError):
        create_directory(Path("test:.dir"))

def test_create_directory_max_length(tmp_path):
    """Test directory creation with maximum length path."""
    long_path = tmp_path / ("a" * 300)
    with pytest.raises(ValueError):
        create_directory(long_path)

def test_create_directory_concurrent():
    """Test concurrent directory creation."""
    import threading
    import time
    
    def create_dir(path):
        time.sleep(0.1)  # Ensure concurrent access
        create_directory(path)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        
        # Create directory concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_dir, args=(test_dir,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert test_dir.exists()
        assert test_dir.is_dir()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
