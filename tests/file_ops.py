"""
Test File Operations
------------------
File operation utilities for testing.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Union

from tests.utils.mock_discord import MockFile
from tests.utils.test_environment import TestEnvironment
import pytest

# Test directory constants
TEST_ROOT = Path("tests")
TEST_DATA_DIR = TEST_ROOT / "data"
TEST_OUTPUT_DIR = TEST_ROOT / "output"
TEST_CONFIG_DIR = TEST_ROOT / "config"
TEST_RUNTIME_DIR = TEST_ROOT / "runtime"
TEST_TEMP_DIR = TEST_ROOT / "temp"
VOICE_QUEUE_DIR = TEST_ROOT / "voice_queue"

@pytest.fixture(scope="session")
def test_env() -> TestEnvironment:
    """Create a test environment for file ops tests."""
    env = TestEnvironment()
    env.setup()
    yield env
    env.cleanup()

@pytest.fixture(autouse=True)
def setup_test_environment(test_env: TestEnvironment):
    """Set up test environment for each test."""
    yield

@pytest.fixture
def test_dir(test_env: TestEnvironment) -> Path:
    """Get test directory."""
    test_dir = test_env.get_test_dir("temp") / "file_ops"
    test_dir.mkdir(exist_ok=True)
    return test_dir

@pytest.fixture
def test_file(test_env: TestEnvironment) -> Path:
    """Create a test file."""
    file_path = test_env.get_test_dir("temp") / "test.txt"
    file_path.write_text("test content")
    return file_path

@pytest.fixture
def test_subdir(test_env: TestEnvironment) -> Path:
    """Create a test subdirectory."""
    subdir = test_env.get_test_dir("temp") / "file_ops" / "subdir"
    subdir.mkdir(exist_ok=True, parents=True)
    return subdir

@pytest.fixture
def test_files(test_env: TestEnvironment) -> list[Path]:
    """Create multiple test files."""
    files = []
    for i in range(3):
        file_path = test_env.get_test_dir("temp") / f"test_{i}.txt"
        file_path.write_text(f"test content {i}")
        files.append(file_path)
    return files

def ensure_test_dirs() -> None:
    """Ensure all test directories exist."""
    for directory in [TEST_DATA_DIR, TEST_OUTPUT_DIR, TEST_CONFIG_DIR, 
                     TEST_RUNTIME_DIR, TEST_TEMP_DIR, VOICE_QUEUE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def safe_remove(path: Union[str, Path]) -> None:
    """Safely remove a file or directory."""
    path = Path(path)
    if path.exists():
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)

def safe_rmdir(path: Union[str, Path], recursive: bool = False) -> None:
    """Safely remove a directory."""
    path = Path(path)
    if path.exists():
        if recursive:
            shutil.rmtree(path)
        else:
            path.rmdir()

def ensure_dir(path: Union[str, Path]) -> None:
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

def get_test_file_path(filename: str, directory: Optional[Path] = None) -> Path:
    """Get path to a test file."""
    if directory is None:
        directory = TEST_DATA_DIR
    return directory / filename

def create_test_file(filename: str, content: str = "", directory: Optional[Path] = None) -> MockFile:
    """Create a test file with content."""
    path = get_test_file_path(filename, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    return MockFile(filename=filename, content=content.encode())

def cleanup_test_environment() -> None:
    """Clean up all test files and directories."""
    test_dirs = [
        TEST_OUTPUT_DIR,
        TEST_RUNTIME_DIR,
        TEST_TEMP_DIR,
        TEST_DATA_DIR,
        TEST_CONFIG_DIR,
        VOICE_QUEUE_DIR
    ]
    for directory in test_dirs:
        if directory.exists():
            shutil.rmtree(directory)
            directory.mkdir(parents=True, exist_ok=True)

def test_safe_mkdir_new(tmp_path):
    """Test safe_mkdir creates new directory."""
    test_dir = tmp_path / "test_dir"
    
    safe_mkdir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
def test_safe_mkdir_existing(tmp_path):
    """Test safe_mkdir handles existing directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Should not raise
    safe_mkdir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
def test_safe_mkdir_file_exists(tmp_path):
    """Test safe_mkdir raises on existing file."""
    test_file = tmp_path / "test_file"
    test_file.write_text("test")
    
    with pytest.raises(FileOpsError):
        safe_mkdir(test_file)
        
def test_safe_mkdir_permission_error(tmp_path):
    """Test safe_mkdir handles permission errors."""
    test_dir = tmp_path / "test_dir"
    
    # Make parent read-only
    os.chmod(tmp_path, 0o444)
    
    with pytest.raises(FileOpsPermissionError):
        safe_mkdir(test_dir)
        
def test_safe_mkdir_concurrent(tmp_path):
    """Test safe_mkdir handles concurrent access."""
    test_dir = tmp_path / "test_dir"
    errors = []
    
    def mkdir_worker():
        try:
            safe_mkdir(test_dir)
        except Exception as e:
            errors.append(e)
            
    # Create multiple threads
    threads = [
        threading.Thread(target=mkdir_worker)
        for _ in range(5)
    ]
    
    # Start all threads
    for t in threads:
        t.start()
        
    # Wait for completion
    for t in threads:
        t.join()
        
    # Verify directory exists
    assert test_dir.exists()
    assert test_dir.is_dir()
    
    # Verify no errors occurred
    assert not errors
    
def test_ensure_dir(tmp_path):
    """Test ensure_dir creates directory."""
    test_dir = tmp_path / "test_dir"
    
    assert ensure_dir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
def test_ensure_dir_failure(tmp_path):
    """Test ensure_dir handles failures."""
    test_dir = tmp_path / "test_dir"
    
    # Make parent read-only
    os.chmod(tmp_path, 0o444)
    
    assert not ensure_dir(test_dir)
    assert not test_dir.exists()
    
def test_clear_dir(tmp_path):
    """Test clear_dir removes contents."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create some files and subdirs
    (test_dir / "file1.txt").write_text("test1")
    (test_dir / "file2.txt").write_text("test2")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file3.txt").write_text("test3")
    
    assert clear_dir(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    assert not list(test_dir.iterdir())
    
def test_archive_file(tmp_path):
    """Test archive_file moves file."""
    source = tmp_path / "source.txt"
    dest = tmp_path / "archive" / "source.txt"
    
    # Create source file
    source.write_text("test content")
    
    assert archive_file(source, dest)
    assert not source.exists()
    assert dest.exists()
    assert dest.read_text() == "test content"
    
def test_archive_file_nonexistent(tmp_path):
    """Test archive_file handles nonexistent source."""
    source = tmp_path / "nonexistent.txt"
    dest = tmp_path / "archive" / "nonexistent.txt"
    
    assert not archive_file(source, dest)
    assert not dest.exists() 
