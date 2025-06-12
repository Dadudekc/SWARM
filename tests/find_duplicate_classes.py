"""
Tests for the duplicate class finder tool.
"""

import os
from pathlib import Path

import pytest

from agent_tools.general_tools.find_duplicate_classes import DuplicateClassFinder

class TestDuplicateClassFinder:
    """Test cases for the DuplicateClassFinder class."""
    
    def test_no_duplicates(self, temp_dir):
        """Test when no duplicate classes exist."""
        # Create test files with unique classes
        (temp_dir / "module1.py").write_text("""
class ClassA:
    def method1(self):
        pass
""")
        (temp_dir / "module2.py").write_text("""
class ClassB:
    def method2(self):
        pass
""")
        
        finder = DuplicateClassFinder(root_dir=str(temp_dir))
        results = finder.find_duplicates()
        
        assert len(results) == 0
    
    def test_exact_duplicates(self, temp_dir):
        """Test detection of exact duplicate classes."""
        # Create test files with identical classes
        class_code = """
class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass
"""
        (temp_dir / "module1.py").write_text(class_code)
        (temp_dir / "module2.py").write_text(class_code)
        
        finder = DuplicateClassFinder(root_dir=str(temp_dir))
        results = finder.find_duplicates()
        
        assert len(results) == 1
        assert results[0]["similarity"] == 1.0
        assert len(results[0]["files"]) == 2
    
    def test_similar_classes(self, temp_dir):
        """Test detection of similar classes."""
        # Create test files with similar classes
        (temp_dir / "module1.py").write_text("""
class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass
""")
        (temp_dir / "module2.py").write_text("""
class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass
    def method3(self):
        pass
""")
        
        finder = DuplicateClassFinder(root_dir=str(temp_dir))
        results = finder.find_duplicates()
        
        assert len(results) == 1
        assert 0.8 <= results[0]["similarity"] < 1.0
        assert len(results[0]["files"]) == 2
    
    def test_different_bases(self, temp_dir):
        """Test detection of classes with different base classes."""
        # Create test files with classes that have different base classes
        (temp_dir / "module1.py").write_text("""
class BaseA:
    pass

class TestClass(BaseA):
    def method1(self):
        pass
""")
        (temp_dir / "module2.py").write_text("""
class BaseB:
    pass

class TestClass(BaseB):
    def method1(self):
        pass
""")
        
        finder = DuplicateClassFinder(root_dir=str(temp_dir))
        results = finder.find_duplicates()
        
        assert len(results) == 1
        assert results[0]["similarity"] > 0.5
        assert len(results[0]["files"]) == 2
    
    def test_min_similarity(self, temp_dir):
        """Test minimum similarity threshold."""
        # Create test files with slightly similar classes
        (temp_dir / "module1.py").write_text("""
class TestClass:
    def method1(self):
        pass
""")
        (temp_dir / "module2.py").write_text("""
class TestClass:
    def method2(self):
        pass
""")
        
        finder = DuplicateClassFinder(root_dir=str(temp_dir), min_similarity=0.8)
        results = finder.find_duplicates()
        
        assert len(results) == 0 