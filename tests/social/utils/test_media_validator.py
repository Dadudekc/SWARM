"""
Test suite for MediaValidator functionality.
"""

import pytest
import os
import tempfile
from dreamos.social.utils.media_validator import MediaValidator

@pytest.fixture
def validator():
    """Create a MediaValidator instance."""
    return MediaValidator()

@pytest.fixture
def temp_file():
    """Create a temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b'test')
    yield f.name
    os.unlink(f.name)

def test_validate_files_empty(validator):
    """Test validating empty file list."""
    is_valid, error = validator.validate_files([])
    assert is_valid is True
    assert error is None

def test_validate_files_single(validator, temp_file):
    """Test validating a single file."""
    is_valid, error = validator.validate_files(temp_file)
    assert is_valid is True
    assert error is None

def test_validate_files_not_found(validator):
    """Test validating non-existent file."""
    is_valid, error = validator.validate_files('nonexistent.jpg')
    assert is_valid is False
    assert error == "File not found: nonexistent.jpg"

def test_validate_files_unsupported_format(validator):
    """Test validating unsupported file format."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'test')
    try:
        is_valid, error = validator.validate_files(f.name)
        assert is_valid is False
        assert error == f"Unsupported format: {f.name}"
    finally:
        os.unlink(f.name)

def test_validate_files_too_large(validator):
    """Test validating file that exceeds size limit."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b'x' * (11 * 1024 * 1024))  # 11MB
    try:
        is_valid, error = validator.validate_files(f.name)
        assert is_valid is False
        assert error == f"File too large: {f.name}"
    finally:
        os.unlink(f.name)

def test_validate_files_too_many(validator, temp_file):
    """Test validating too many files."""
    files = [temp_file] * 21  # More than max_files
    is_valid, error = validator.validate_files(files)
    assert is_valid is False
    assert error == "Too many files (max: 20)"

def test_validate_media_video(validator):
    """Test validating video file."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b'test')
    try:
        is_valid, error = validator.validate_media(f.name, is_video=True)
        assert is_valid is True
        assert error is None
    finally:
        os.unlink(f.name)

def test_validate_media_video_wrong_format(validator):
    """Test validating non-video file as video."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b'test')
    try:
        is_valid, error = validator.validate_media(f.name, is_video=True)
        assert is_valid is False
        assert error == f"Not a video file: {f.name}"
    finally:
        os.unlink(f.name)

def test_validate_single_file(validator, temp_file):
    """Test validate() method (alias for validate_files)."""
    is_valid, error = validator.validate(temp_file)
    assert is_valid is True
    assert error is None 